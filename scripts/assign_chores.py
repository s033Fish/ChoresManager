import sqlite3
import random
from datetime import datetime, timedelta, date

def get_user_week():
    """
    Prompt the user for the Monday of the week they want to assign chores for.
    """
    print("Enter the date for the Monday of the week you want to assign chores (YYYY-MM-DD).")
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

def get_unassigned_chores(cursor, start_date, end_date):
    """
    Fetch all chores for the specified week that are not yet assigned to any user.
    """
    query = """
        SELECT id, day_of_week, meal_time, date
        FROM chores_manager_chore
        WHERE user_id IS NULL AND date BETWEEN ? AND ?;
    """
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchall()

def get_users(cursor):
    """
    Fetch all users from the database.
    """
    query = """
        SELECT id, first_name, last_name
        FROM auth_user;
    """
    cursor.execute(query)
    return cursor.fetchall()

def assign_chores(cursor, conn, unassigned_chores, users):
    """
    Randomly assign users to unassigned chores.
    """
    if not users:
        print("No users available to assign chores.")
        return

    for chore in unassigned_chores:
        chore_id, day_of_week, meal_time, chore_date = chore
        assigned_user = random.choice(users)  # Randomly pick a user
        user_id = assigned_user[0]

        # Assign the user to the chore
        cursor.execute(
            """
            UPDATE chores_manager_chore
            SET user_id = ?
            WHERE id = ?;
            """,
            (user_id, chore_id)
        )
        print(f"Assigned {assigned_user[1]} {assigned_user[2]} to {day_of_week} ({chore_date}) - {meal_time}.")

    conn.commit()
    print("All unassigned chores for the selected week have been updated.")

def main():
    # Connect to the SQLite database
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Prompt the user for the week to assign chores
    start_of_week, end_of_week = get_user_week()
    print(f"Assigning unassigned chores for the week: {start_of_week} to {end_of_week}")

    # Fetch unassigned chores and available users
    unassigned_chores = get_unassigned_chores(cursor, start_of_week, end_of_week)
    users = get_users(cursor)

    if not unassigned_chores:
        print("No unassigned chores found for the selected week.")
    else:
        assign_chores(cursor, conn, unassigned_chores, users)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()

