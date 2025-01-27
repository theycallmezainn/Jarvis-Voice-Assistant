import streamlit as st
import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser
import os
import smtplib
import requests
import threading
import pandas as pd
import matplotlib.pyplot as plt

# Provide the absolute path to your image or verify the relative path
image_path = 'G:/image/images.jpg'  # Update with the full path if necessary

# Add background image and remove hover effect using Streamlit's markdown support
st.markdown(
    f"""
    <style>
        .reportview-container {{
            background: url('{image_path}');
            background-size: cover;
            background-position: center;
            height: 100%;
        }}
        .sidebar .sidebar-content {{
            background: rgba(0, 0, 0, 0.3);
        }}
        .stButton > button {{
            background-color: transparent;
            color: black;
            border: 1px solid black;
        }}
        .stButton > button:hover {{
            background-color: transparent;
            color: black;
            border: 1px solid black;
        }}
        .stTextInput input {{
            color: black;
        }}
        .stMarkdown {{
            color: black;
        }}
    </style>
    """, unsafe_allow_html=True)

# Initialize the pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Initialize the speech engine
def speak(audio):
    def speak_thread():
        engine.say(audio)
        engine.runAndWait()

    threading.Thread(target=speak_thread).start()

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        speak("Good Morning")
    elif hour >= 12 and hour < 18:
        speak("Good Afternoon")
    else:
        speak("Good Evening")
    speak("Jarvis here, how may I help you?")

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        st.write("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        st.write(f"User said: {query}")
    except Exception as e:
        st.write("Sorry, please say that again.")
        return "None"
    return query

def sendEmail(to, content):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login('<EMAIL>', '<PASSWORD>')  # Replace with your credentials
        server.sendmail('<EMAIL>', to, content)
        server.close()
        speak("Email has been sent successfully.")
    except Exception as e:
        speak("Sorry, I was unable to send the email.")
        st.write(e)

def getWeather(city):
    api_key = "640c0e3522649003e29ef45734a1c3a0"  # Your actual API key
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"  # For temperature in Celsius
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if data.get("cod") == 200:  # Check if the response is successful
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            result = f"The weather in {city} is currently {weather_desc} with a temperature of {temp}°C and humidity of {humidity}%."

            # Store the city and temperature in session state
            if "weather_searches" not in st.session_state:
                st.session_state.weather_searches = []

            st.session_state.weather_searches.append({"City": city, "Temperature": temp, "Humidity": humidity})
            return result
        else:
            error_message = data.get("message", "Unknown error")
            return f"Error: {error_message}. Please try again with a valid city name."
    except Exception as e:
        return "Sorry, I couldn't fetch the weather details."

def getNews(keyword):
    api_key = "a3bdde8225cb44afb4f6cf915ef62413"
    base_url = "https://newsapi.org/v2/everything"
    params = {
        "q": keyword,
        "apiKey": api_key,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5  # Fetch the top 5 articles
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if data["status"] == "ok":  # Check if the response is successful
            articles = data.get("articles", [])
            news_list = []
            for article in articles:
                title = article["title"]
                description = article["description"]
                url = article["url"]
                news_list.append(f"- **{title}**\n{description}\n[Read more]({url})\n")
            return news_list
        else:
            return [f"Error fetching news: {data.get('message', 'Unknown error')}"]
    except Exception as e:
        return ["Sorry, I couldn't fetch the news."]

# Streamlit App code
def main():
    st.title("Jarvis - Voice Assistant")

    # Initialize session state for weather searches
    if "weather_searches" not in st.session_state:
        st.session_state.weather_searches = []

    # Wish the user
    wishMe()

    # Button to talk to Jarvis
    if st.button("Talk to Jarvis", key="talk_to_jarvis"):
        st.write("Listening...")
        user_command = takeCommand().lower()

        if user_command != "None":
            if "weather" in user_command:
                city = user_command.replace("weather", "").strip()
                if city:
                    st.write(f"Getting weather for {city}...")
                    weather_report = getWeather(city)
                    st.write(weather_report)
                    speak(weather_report)
                else:
                    st.write("Please mention the city name after 'weather'.")
                    speak("Please mention the city name after 'weather'.")

            elif "news" in user_command:
                keyword = user_command.replace("news", "").strip()
                if keyword:
                    st.write(f"Fetching news for '{keyword}'...")
                    news_list = getNews(keyword)
                    for news in news_list:
                        st.write(news)
                        speak(news)
                else:
                    st.write("Please mention the topic for news updates.")
                    speak("Please mention the topic for news updates.")

            elif 'exit' in user_command or 'quit' in user_command:
                st.write("Goodbye, have a nice day!")
                speak("Goodbye, have a nice day!")
                st.stop()

    # Button to download CSV with a unique key
    if st.button("Download Weather Data as CSV", key="download_csv"):
        if st.session_state.weather_searches:
            df = pd.DataFrame(st.session_state.weather_searches)
            csv = df.to_csv(index=False)
            st.download_button(label="Download CSV", data=csv, file_name="weather_data.csv", mime="text/csv")
        else:
            st.write("No weather data to download.")

    # Button to show graph with a unique key
    if st.button("Show Weather Graph", key="show_graph"):
        if st.session_state.weather_searches:
            df = pd.DataFrame(st.session_state.weather_searches)
            avg_temp = df.groupby("City")["Temperature"].mean()

            # Plot the graph
            plt.figure(figsize=(8, 5))
            avg_temp.plot(kind='bar', color='skyblue', edgecolor='black')
            plt.title("Average Temperature by City", fontsize=16)
            plt.ylabel("Temperature (°C)", fontsize=12)
            plt.xlabel("City", fontsize=12)
            plt.xticks(rotation=45)
            st.pyplot(plt)

if __name__ == '__main__':
    main()
