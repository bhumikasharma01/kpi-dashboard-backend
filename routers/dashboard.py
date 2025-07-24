from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from core.security import get_current_user
from io import BytesIO
from database import get_db
from sqlalchemy.orm import Session
from models import UploadedReport,User
import pandas as pd
import os
from datetime import datetime

router = APIRouter(
    prefix="/kpi",
    tags=["dashboard"]
)


UPLOAD_FOLDER = 'uploads'





@router.get("/dashboard")
def get_dashboard_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        now = datetime.now()
        current_month = now.strftime("%B")
        current_year = now.year

        # 🔍 Query the uploaded report from the database
        report = db.query(UploadedReport).filter(
            UploadedReport.month == current_month,
            UploadedReport.year == current_year
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail=f"No report found for {current_month} {current_year}")

        # ✅ Load Excel file from DB binary content
        file_content = BytesIO(report.content)
        df = pd.read_excel(file_content, header=None)

        # Extract rows
        labels = df.iloc[:, 0].astype(str).str.strip().str.lower()
        count_row = df[labels == 'total count overall'].index[0]
        rank_row = df[labels == 'rank overall'].index[0]
        cluster_row = df[labels == 'cluster'].index[0]

        counts = df.iloc[count_row, 1:].tolist()
        ranks = df.iloc[rank_row, 1:].tolist()
        clusters = df.iloc[cluster_row, 1:].tolist()

        ranking_df = pd.DataFrame({
            'Cluster': clusters,
            'Total Count Overall': counts,
            'Rank': ranks
        })

        ranking_df = ranking_df.dropna()
        ranking_df['Total Count Overall'] = pd.to_numeric(ranking_df['Total Count Overall'], errors='coerce')
        ranking_df['Rank'] = pd.to_numeric(ranking_df['Rank'], errors='coerce').astype(int)
        ranking_df = ranking_df.dropna().sort_values(by='Rank').reset_index(drop=True)

        podium = ranking_df.head(3).sort_values(by='Rank').reset_index(drop=True)

        return {
            "month": current_month,
            "year": current_year,
            "podium": podium.to_dict(orient='records'),
            "rankings": ranking_df.to_dict(orient='records')
        }
    except Exception as e:
        import traceback
        traceback.print_exc()  # <== shows full error in terminal
        print(f"❌ Error in get_dashboard_data: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

    
