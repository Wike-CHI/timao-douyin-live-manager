from server.app.database import DatabaseManager
from server.config import DatabaseConfig
from server.app.models.live import LiveSession
from server.app.models.live_review import LiveReviewReport

dm = DatabaseManager(DatabaseConfig())
dm.initialize()

with dm.get_session() as db:
    sessions = db.query(LiveSession).all()
    reports = db.query(LiveReviewReport).all()
    
    print("\n直播会话:")
    for s in sessions:
        print(f"  会话{s.id}: room={s.room_id}, status={s.status}, duration={s.duration}s, title={s.title}")
    
    print("\n复盘报告:")
    for r in reports:
        print(f"  报告{r.id}: session_id={r.session_id}, score={r.overall_score}, has_charts={bool(r.trend_charts)}")
    
    print(f"\n总计: {len(sessions)}个会话, {len(reports)}个报告\n")
