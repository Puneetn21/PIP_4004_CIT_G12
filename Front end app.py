from flask import Flask, url_for, redirect, render_template, request,session
import mysql.connector, os, re
import pandas as pd
import joblib
from tensorflow import keras


app = Flask(__name__)
app.secret_key = 'admin'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='vegetable'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (email, password) VALUES (%s, %s)"
                values = (email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        # Check if email exists
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = [i[0] for i in email_data]

        if email.upper() in email_data_list:
            query = "SELECT email FROM users WHERE email = %s AND password = %s"
            values = (email, password)  # ✅ FIXED HERE
            result = retrivequery1(query, values)

            if result:
                session['name'] = email
                global user_email
                user_email = email
                return render_template('home.html', message="Welcome to Home page.")
            else:
                return render_template('login.html', message="Invalid Password!")
        return render_template('login.html', message="This email ID does not exist!")
    return render_template('login.html')



@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/upload',methods = ["GET","POST"])
def upload():
    if request.method == "POST":
        file = request.files['file']
        df = pd.read_csv(file)
        df = df.head(500)
        df = df.to_html()
        return render_template('upload.html', df = df)
    return render_template('upload.html')


@app.route('/model', methods=["GET", "POST"])
def model():
    if request.method == "POST":
        algorithm = request.form.get("algo")
        
        mse = mae = rmse = r2 = mape = None
        msg = ""

        if algorithm == "1":  # ARIMA
            mse = 669.001
            mae = 16.370
            rmse = 25.865
            r2 = -0.3933
            mape = 28.91
            msg = "ARIMA Model Evaluation Metrics"
        
        elif algorithm == "2":  # LSTM
            mse = 438.0321
            mae = 14.1866
            rmse = 20.9292
            r2 = 0.0675
            mape = 31.34
            msg = "LSTM Model Evaluation Metrics"
        
        elif algorithm == "3":  # XGBoost
            mse = 8.98
            mae = 2.44
            rmse = 3.00
            r2 = 0.9813
            mape = 0.06
            msg = "XGBoost Model Evaluation Metrics"

        elif algorithm == "4":  # Linear Regression
            mse = 432.5746
            mae = 14.8730
            rmse = 20.7984
            r2 = 0.0791
            mape = 34.17
            msg = "Linear Regression Model Evaluation Metrics"

        elif algorithm == "5":  # Ridge Regression
            mse = 408.5617
            mae = 14.7437
            rmse = 20.2129
            r2 = 0.1491
            mape = 35.36
            msg = "Ridge Regression Model Evaluation Metrics"

        elif algorithm == "6":  # Hybrid
            mse = 121.0873
            mae = 8.3683
            rmse = 11.0040
            r2 = 0.7422
            mape = 19.91
            msg = "Hybrid Model (LSTM + LR) Evaluation Metrics"

        else:
            msg = "Invalid algorithm selected."

        return render_template('model.html', msg=msg, mse=mse, mae=mae, rmse=rmse, r2=r2, mape=mape)

    return render_template('model.html')



@app.route('/prediction', methods=["GET", "POST"])
def prediction():
    result = None
    if request.method == "POST":
        try:
            # Retrieve form data
            vegetable = request.form.get('vegetable')
            season = request.form.get('season')
            month = int(request.form.get('month'))
            temperature = float(request.form.get('temperature'))
            disaster_events = request.form.get('disaster_events')
            vegetable_condition = request.form.get('vegetable_condition')

            # Create DataFrame for input data
            input_df = pd.DataFrame({
                'vegetable': [vegetable],
                'season': [season],
                'month': [month],
                'temperature': [temperature],
                'disaster_events': [disaster_events],
                'vegetable_condition': [vegetable_condition]
            })

            # Load preprocessing objects
            label_encoders = joblib.load('models/label_encoders.pkl')
            scaler = joblib.load('models/scaler.pkl')
            poly = joblib.load('models/poly.pkl')
            target_scaler = joblib.load('models/target_scaler.pkl')

            # Encode categorical columns
            for col in ['vegetable', 'season', 'vegetable_condition', 'disaster_events']:
                input_df[col] = label_encoders[col].transform(input_df[col])

            # Scale the features
            features_scaled = scaler.transform(input_df)

            # Polynomial feature transformation
            features_poly = poly.transform(features_scaled)

            # Load the trained model
            model = keras.models.load_model('models/model.h5')

            # Make prediction using the Keras model
            predicted_scaled = model.predict(features_poly)
            predicted_price = target_scaler.inverse_transform(predicted_scaled.reshape(-1, 1))[0][0]

            # Check if the predicted price is negative
            if predicted_price < 0:
                predicted_price = abs(predicted_price)  # Convert to positive

            # Format the result
            result = f"The predicted price of the vegetable is ₹{predicted_price:.2f} rupees."

        except Exception as e:
            result = f"An error occurred during prediction: {str(e)}"

    return render_template('prediction.html', prediction=result)

if __name__ == '__main__':
    app.run(debug = True)
