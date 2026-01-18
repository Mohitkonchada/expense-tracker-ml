from flask import Flask, render_template, request
import csv
import os
import pandas as pd
from sklearn.linear_model import LinearRegression
import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    message = ""
    prediction = None
    monthly_total = 0
    expenses_list = []

    # Handle form submission
    if request.method == 'POST':
        date = request.form.get('date')
        amount = request.form.get('amount')
        category = request.form.get('category')

        # Save to CSV
        file_exists = os.path.isfile('expenses.csv')
        with open('expenses.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Date', 'Amount', 'Category'])
            writer.writerow([date, amount, category])

        message = f"Expense Added: {date}, {amount}, {category}"

    # Read CSV if exists
    if os.path.isfile('expenses.csv'):
        df = pd.read_csv('expenses.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        expenses_list = df.to_dict('records')

        # Calculate monthly total
        now = datetime.datetime.now()
        monthly_total = df[(df['Date'].dt.month == now.month) & (df['Date'].dt.year == now.year)]['Amount'].astype(float).sum()

        # ML Prediction
        df['DayNumber'] = df['Date'].map(lambda x: x.toordinal())
        X = df[['DayNumber']]
        y = df['Amount'].astype(float)
        model = LinearRegression()
        model.fit(X, y)
        last_date = df['Date'].max()
        next_month_date = last_date + pd.DateOffset(months=1)
        next_day_number = next_month_date.toordinal()
        prediction = round(model.predict([[next_day_number]])[0], 2)

    return render_template('index.html', message=message, prediction=prediction, expenses=expenses_list, monthly_total=monthly_total)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
