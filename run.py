from app import app, db


def ensure_db_created() -> None:
	# Create tables on first run
	with app.app_context():
		db.create_all()


if __name__ == "__main__":
	ensure_db_created()
	app.run(debug=True)


