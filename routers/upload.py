from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
import io
from fastapi.responses import StreamingResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session
from database import get_db
from fastapi.responses import JSONResponse
from core.security import get_current_user
from models import User,UploadedReport,GeneratedReport
from datetime import datetime
from fastapi import Form,Query
from datetime import timezone
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3
from datetime import datetime,timedelta
from PyPDF2 import PdfReader
import re
from fastapi.responses import JSONResponse
import base64








router = APIRouter(prefix="/upload", tags=["upload"])




import traceback

@router.post("/reports")
async def upload_report(
    month: str = Form(...),
    year: int = Form(...),
    replace: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        print(f"📁 Upload started for: {month}-{year}, file: {file.filename}, by: {current_user.username}")
        
        existing = db.query(UploadedReport).filter(
            and_(UploadedReport.month == month, UploadedReport.year == year)
        ).first()

        if existing:
            print("⚠️ Existing report found")
            if not replace:
                return {"error": "exists", "filename": existing.filename}
            db.delete(existing)
            db.commit()

        contents = await file.read()
        print(f"📄 File size: {len(contents)} bytes")

        report = UploadedReport(
            filename=f"{year}_{month}_Report.xlsx",
            uploaded_by=current_user.username,
            month=month,
            year=year,
            content=contents,
           
            #uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        print("✅ Upload successful")
        
        return {"message": "✅ Report uploaded successfully", "filename": report.filename}


    except Exception as e:
        print("❌ Exception during upload_report:")
        traceback.print_exc()  # Show full traceback in console
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.get("/reports")
def get_all_reports(
    month: str = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(UploadedReport)

        if month:
            query = query.filter(UploadedReport.month == month)
        if year:
            query = query.filter(UploadedReport.year == year)

        reports = query.all()

        result = []
        for r in reports:
            result.append({
                "id": r.id,
                "filename": r.filename,
                "uploaded_by": r.uploaded_by,
                "month": r.month,
                "year": r.year,
                
            })

        return result

    except Exception as e:
        print(f"❌ Error in GET /upload/reports: {e}")
        raise HTTPException(status_code=500, detail="Server error during report fetch")




@router.get("/reports/download")
def download_report(
    month: str = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(UploadedReport).filter(
        and_(UploadedReport.month == month, UploadedReport.year == year)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return StreamingResponse(
        io.BytesIO(report.content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={report.filename}"}
    )
@router.delete("/reports/delete")
def delete_report(
    month: str = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(UploadedReport).filter(
        and_(
            UploadedReport.month == month,
            UploadedReport.year == year
        )
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    return {"message": f"Report for {month} {year} deleted successfully"}
@router.get("/view")
def view_report_by_month(
    month: str = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 🔍 Fetch report from DB
        report = db.query(UploadedReport).filter(
            UploadedReport.month == month,
            UploadedReport.year == year
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail=f"❌ No report found for {month} {year}")

        file_content = BytesIO(report.content)
        df = pd.read_excel(file_content, header=None)

        labels = df.iloc[:, 0].astype(str).str.strip().str.lower()

        try:
            count_row = df[labels == 'total count overall'].index[0]
            rank_row = df[labels == 'rank overall'].index[0]
            cluster_row = df[labels == 'cluster'].index[0]
        except IndexError:
            raise HTTPException(status_code=400, detail="❌ Required labels (Cluster, Rank, Total Count) not found in the file.")

        counts = df.iloc[count_row, 1:].tolist()
        ranks = df.iloc[rank_row, 1:].tolist()
        clusters = df.iloc[cluster_row, 1:].tolist()

        # 🧹 Trim all lists to same size
        min_len = min(len(counts), len(ranks), len(clusters))

        ranking_df = pd.DataFrame({
            'Cluster': clusters[:min_len],
            'Total Count Overall': counts[:min_len],
            'Rank': ranks[:min_len]
        })

        ranking_df.dropna(inplace=True)
        ranking_df['Total Count Overall'] = pd.to_numeric(ranking_df['Total Count Overall'], errors='coerce')
        ranking_df['Rank'] = pd.to_numeric(ranking_df['Rank'], errors='coerce').astype('Int64')
        ranking_df = ranking_df.dropna(subset=['Cluster', 'Total Count Overall', 'Rank'])
        ranking_df = ranking_df.sort_values(by='Rank').reset_index(drop=True)

        podium = ranking_df.head(3).sort_values(by='Rank').reset_index(drop=True)

        return {
            "month": month,
            "year": year,
            "podium": podium.to_dict(orient='records'),
            "rankings": ranking_df.to_dict(orient='records')
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error in view_report_by_month: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/reports/all")
def get_all_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = db.query(UploadedReport).all()
    return [{"id": r.id, "filename": r.filename} for r in reports]

@router.get("/download_pdf/{pdf_id}")
def download_pdf(pdf_id: int, db: Session = Depends(get_db)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == pdf_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="PDF report not found")

    return StreamingResponse(
        BytesIO(report.pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report.pdf_filename}"}

    )

# Add this to your upload.py file



@router.post("/generate_pdf")
def generate_and_store_pdf(
    month: str = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # 📄 Fetch the corresponding uploaded report
    uploaded_report = db.query(UploadedReport).filter_by(month=month, year=year).first()
    if not uploaded_report:
        raise HTTPException(status_code=404, detail="No uploaded report found")

    file_content = BytesIO(uploaded_report.content)
    df = pd.read_excel(file_content, header=None)
    labels = df.iloc[:, 0].astype(str).str.strip().str.lower()

    try:
        count_row = df[labels == 'total count overall'].index[0]
        rank_row = df[labels == 'rank overall'].index[0]
        cluster_row = df[labels == 'cluster'].index[0]
    except IndexError:
        raise HTTPException(status_code=400, detail="Required rows not found in Excel file")

    counts = df.iloc[count_row, 1:].tolist()
    ranks = df.iloc[rank_row, 1:].tolist()
    clusters = df.iloc[cluster_row, 1:].tolist()

    min_len = min(len(counts), len(ranks), len(clusters))

    ranking_df = pd.DataFrame({
        'Cluster': clusters[:min_len],
        'Total Count Overall': counts[:min_len],
        'Rank': ranks[:min_len]
    })

    ranking_df.dropna(inplace=True)
    ranking_df['Total Count Overall'] = pd.to_numeric(ranking_df['Total Count Overall'], errors='coerce')
    ranking_df['Rank'] = pd.to_numeric(ranking_df['Rank'], errors='coerce').astype('Int64')
    ranking_df = ranking_df.dropna(subset=['Cluster', 'Total Count Overall', 'Rank'])
    ranking_df = ranking_df.sort_values(by='Rank').reset_index(drop=True)

    # 📄 Create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Full Rankings - {month} {year}")

    c.setFont("Helvetica", 12)
    table_y = height - 100

    c.drawString(50, table_y, f"{'Cluster':<30} {'Total Count Overall':<25} {'Rank':<10}")
    table_y -= 20

    for _, row in ranking_df.iterrows():
        c.drawString(50, table_y, f"{row['Cluster']:<30} {row['Total Count Overall']:<25} {row['Rank']:<10}")
        table_y -= 20
        if table_y < 50:
            c.showPage()
            table_y = height - 50

    c.save()
    buffer.seek(0)

    pdf_filename = f"Full_Rankings_{month}_{year}.pdf"
    pdf_bytes = buffer.getvalue()

    # 🗃️ Save PDF to database
    new_pdf = GeneratedReport(
        pdf_filename=pdf_filename,
        pdf_content=pdf_bytes,
        uploaded_report_id=uploaded_report.id
    )

    db.add(new_pdf)
    db.commit()
    db.refresh(new_pdf)

    return {"message": "✅ PDF generated and stored successfully", "pdf_id": new_pdf.id, "filename": pdf_filename}

# @router.get("/reports/last-3-months")
# def get_reports_last_3_months(db: Session = Depends(get_db)):
#     three_months_ago = datetime.utcnow() - timedelta(days=90)
#     reports = db.query(UploadedReport)\
#                 .filter(UploadedReport.uploaded_at >= three_months_ago)\
#                 .order_by(UploadedReport.uploaded_at.desc())\
#                 .all()
#     return reports
@router.get("/reports/last-three-months")
def get_last_three_reports():
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Get current date
        today = datetime.today()

        # Compute the first day of the current month
        first_of_this_month = datetime(today.year, today.month, 1)

        # Compute the first day of the month 3 months ago
        three_months_ago = (first_of_this_month - timedelta(days=90)).replace(day=1)

        cursor.execute("""
            SELECT id, pdf_filename, generated_at
            FROM generated_reports
            WHERE DATE(generated_at) >= DATE(?)
            ORDER BY generated_at DESC
        """, (three_months_ago,))
        
        rows = cursor.fetchall()

        reports = []
        for row in rows:
            generated_date = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f")
            reports.append({
                "id": row[0],
                "filename": row[1],
                "month": generated_date.strftime("%B"),
                "year": generated_date.year,
                "metrics": {
                    "Score": 85 + row[0],  # Dummy metric for now
                    "Accuracy": 90 + row[0] % 10
                }
            })

        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all_generated")
def get_all_generated_reports(db: Session = Depends(get_db)):
    reports = db.query(GeneratedReport).all()

    result = []
    for r in reports:
        result.append({
            "id": r.id,
            "pdf_filename": r.pdf_filename,
            "pdf_content": base64.b64encode(r.pdf_content).decode("utf-8"),
            "generated_at": r.generated_at.isoformat()
        })

    return result


@router.get("/cluster_ranks")
def get_cluster_rank_trend(cluster_name: str = Query(...), db: Session = Depends(get_db)):
    cluster_name = cluster_name.strip().lower()

    reports = db.query(GeneratedReport).order_by(GeneratedReport.generated_at.desc()).limit(6).all()

    trend_data = []
    for report in reports:
        pdf = PdfReader(BytesIO(report.pdf_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

        # Match the line with the cluster
        pattern = rf"^{cluster_name}\s+(\d+)\s+(\d+)"
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)

        if match:
            count = int(match.group(1))
            rank = int(match.group(2))
            trend_data.append({
                "month": report.pdf_filename.split('_')[2],  # e.g. Full_Rankings_July_2025.pdf
                "year": report.pdf_filename.split('_')[3].replace('.pdf', ''),
                "rank": rank,
                "count": count
            })

    if not trend_data:
        raise HTTPException(status_code=404, detail="Cluster not found in recent reports")

    return sorted(trend_data, key=lambda x: (x['year'], x['month']))
   
    
