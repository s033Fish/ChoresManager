import sqlite3
from datetime import date, timedelta, datetime

# Register adapters and converters for SQLite to handle date and datetime objects
def adapt_date(d):
    return d.isoformat()

def convert_date(s):
    return date.fromisoformat(s.decode("utf-8"))

sqlite3.register_adapter(date, adapt_date)
sqlite3.register_converter("DATE", convert_date)

# Constants
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MEAL_TIMES = ['Breakfast', 'Lunch', 'Dinner']

def get_user_week():
    """
    Prompt the user for the week they want to update. Default to the current week.
    """
    print("Enter the date for the Monday of the week you want to update (YYYY-MM-DD).")
    user_input = input("Leave blank to use the current week: ").strip()
    
    try:
        if user_input:
            start_of_week = datetime.strptime(user_input, "%Y-%m-%d").date()
            if start_of_week.weekday() != 0:
                print("The entered date is not a Monday. Please try again.")
                return get_user_week()
        else:
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())  # Default to current week's Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday of the same week
        return start_of_week, end_of_week
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return get_user_week()

def get_existing_chores(cursor, start_date, end_date):
    """
    Fetch chores for the given date range from the database.
    """
    query = """
        SELECT date, day_of_week, meal_time
        FROM chores_manager_chore
        WHERE date BETWEEN ? AND ?;
    """
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchall()

def populate_missing_chores(cursor, conn, start_date, end_date):
    """
    Populate chores for the week and prompt the user for missing chores.
    """
    existing_chores = get_existing_chores(cursor, start_date, end_date)
    existing_set = {(row[0], row[1], row[2]) for row in existing_chores}

    for i in range(7):  # 7 days in the week
        chore_date = start_date + timedelta(days=i)
        day_of_week = DAYS_OF_WEEK[i]

        for meal_time in MEAL_TIMES:
            if (chore_date, day_of_week, meal_time) not in existing_set:
                print(f"No chore exists for {day_of_week} ({chore_date}) - {meal_time}.")
                response = input("Would you like to add this chore? (yes/no): ").strip().lower()

                if response in ['yes', 'y']:
                    cursor.execute(
                        """
                        INSERT INTO chores_manager_chore (day_of_week, meal_time, completed, date)
                        VALUES (?, ?, 0, ?);
                        """,
                        (day_of_week, meal_time, chore_date)
                    )
                    print(f"Added chore for {day_of_week} ({chore_date}) - {meal_time}.")
                else:
                    print(f"Skipped adding chore for {day_of_week} ({chore_date}) - {meal_time}.")

    conn.commit()
    print("Chore population completed.")

def main():
    # Connect to the SQLite database with custom converters
    conn = sqlite3.connect("db.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()

    # Prompt user for the week to update
    start_of_week, end_of_week = get_user_week()
    print(f"Populating chores for the week: {start_of_week} to {end_of_week}")
    populate_missing_chores(cursor, conn, start_of_week, end_of_week)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()

