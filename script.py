from bs4 import BeautifulSoup as bs4
import requests
import re
from datetime import datetime
from validate_email import validate_email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pymysql as MySQLdb
from warnings import filterwarnings
import time
import argparse

# following code to take inputs from the command line
parser = argparse.ArgumentParser()
parser.add_argument('email_add', help="Please entert the sender email address "
                    "through which you want to send the mails")
parser.add_argument('password', help="Please enter the password of your "
                    "email account")
parser.add_argument('user', help="Please entert the MySql User")
parser.add_argument('passw', help="Please enter the password of your"
                    " MySql Database")
args = parser.parse_args()


# takes tv series names and dumbs in database
def intake_tvseries():
    tvseries = input("Enter your series( comma seperated):"
                     "Please be careful with the spellings:\n")
    # verify if user has entered data or not
    if len(tvseries) == 0:
        print("Field can't be blank")
        return intake_tvseries()
    else:
        return tvseries


# verifies email of the users
def verify(email_add):
    if (validate_email(email_add) and validate_email(email_add, check_mx=True)
       and validate_email(email_add, verify=True)):
        return True
    else:
        return False


# scraps IMDB ids of given Tv Shows
def get_titles_id(epi_name):
    url = "https://www.imdb.com/find?ref_=nv_sr_fn&q="+epi_name+"&s=all"
    try:
        web_page = requests.get(url)
        soup_title = bs4(web_page.content, 'html.parser')
        # these variables store the data fetched from scrapping
        filtered_1 = soup_title.find("div", {"class": "findSection"})
        filtered_2 = filtered_1.find("table", {"class": "findList"})
        extension = filtered_2.find("a", href=True)["href"].split('?')[0]
        return extension  # gives url of particular series IMDB page
    except Exception as e:
        #  print(e)
        print("Either there is connectivity problem or the "
              "Episode Names:- {} is wrong".format(epi_name))
        return "Fault"


# gets link to the page we are concerned with
def get_main_page(epi_name):
    extension = get_titles_id(epi_name)
    if extension == 'Fault':
        return 'Fault'
    else:
        url = 'https://www.imdb.com'+extension+'episodes?ref_=tt_ql_tv_1'
        try:
            web_page = requests.get(url)
            soup_main = bs4(web_page.content, 'html.parser')
            # stores elements required in further functions
            elements = [soup_main, extension]
            return elements
        except Exception as e:
            #  print(e)
            print("There is connectivity problem, Please Try Again")
            return 'Fault'


# tells if the series has ended
def series_has_ended(epi_name):
    elements = get_main_page(epi_name)
    if elements == 'Fault':
        return 'Fault'
    else:
        try:
            soup_main = elements[0]
            filtered = soup_main.find("meta",  property="og:title")
            num = filtered['content'].find('–')
        except Exception as e:
            #  print(e)
            return 'Fault'
        # returns true if the series has ended
        if filtered['content'][num+1].isdigit():
            return True
        else:
            return elements


# gives info about the upcoming season
def next_season(elements):
    exten = ""
    url_next = ""
    soup_main = elements[0]
    extension = elements[1]
    try:
        filtered_1 = soup_main.find_all("div", {"class": "clear", "itemtype":
                                        "http://schema.org/TVSeason"})
        exten = filtered_1[0].find_all("a", {"id":
                                       "load_next_episodes"})[0]['href']
        url_next = 'https://www.imdb.com'+extension+'episodes'+exten
        web_page = requests.get(url_next)
        soup_next = bs4(web_page.content, 'html.parser')
        epi_data = soup_next.find_all(
            "div", {'class': 'info', 'itemprop': "episodes"})
        a = epi_data[0].find("div", {'class': 'airdate'})
        # returns the date
        return a.text.strip()
    except Exception as e:
        #  print(e)
        return None


# gives info about the upcoming episode
def next_episode(elements):
    soup_main = elements[0]
    try:
        filtered_1 = soup_main.find_all("div", {"class": "clear", "itemtype":
                                        "http://schema.org/TVSeason"})
        text = str(filtered_1).split()
        epi_no = int(re.findall(r'\d+', text[5])[0])
        epi_data = soup_main.find_all(
            "div", {'class': 'info', 'itemprop': "episodes"})
        date = epi_data[epi_no-1].find("div", {'class': 'airdate'})
    except Exception as e:
        #  print(e)
        return "Fault"
    if len(date.text.strip()) > 0:
        present = datetime.now()
        datetime_object = datetime.strptime(
            date.text.strip().replace('.', ''), '%d %b  %Y')
        # check if episode is new or old
        if present > datetime_object:
            return True
        else:
            return date.text.strip()
    else:
        try:
            epi_data = soup_main.find_all("div", {'class': "header",
                                          'id': "episodes_content"})
            date = epi_data[0].find("h3", {'id': "nextEpisode"}).find("span")
            return date.text[5:-1].strip()
        except Exception as e:
            #  print(e)
            return False

    return False


# IMDB scrapper
def scrapping_imdb(tvseries):
    series = []
    message_dict = dict()
    msg = ''
    # checking for empty string
    for episode in tvseries.split(','):
        if len(episode) > 0:
            series.append(episode)
    # checks all the above conditions for each entered Tv Shows
    for name in series:
        name = name.strip()
        returned_content = series_has_ended(name)
        if returned_content is True:
            message_dict[name] = ("The show has finished "
                                  "streaming all its episodes.")
        elif returned_content == 'Fault':
            message_dict[name] = ("Plese check the TvSeries name "
                                  "entered, could not fetch data.")
        else:
            season_content = next_season(returned_content)
            if season_content is not None:
                message_dict[name] = ("The next season begins "
                                      "in "+season_content+'.')
            else:
                episode_content = next_episode(returned_content)
                if episode_content == 'Fault':
                    message_dict[name] = ("Plese check the TvSeries name, "
                                          "entered, could not fetch data.")
                elif episode_content is True:
                    message_dict[name] = ("All episodes are over in current "
                                          "season. Sorry, no info "
                                          "about later season.")
                elif episode_content is False:
                    message_dict[name] = ("There is an upcoming episode but "
                                          "no details provided, Stay tuned.")
                else:
                    conv = time.strptime(episode_content.replace('.', ''),
                                         '%d %b  %Y')
                    message_dict[name] = "Next episode airs on " + \
                        time.strftime("%Y-%m-%d", conv)+"."
    for key, value in message_dict.items():
        msg = msg + ("Tv series name: " + key.upper().strip() + '\nStatus: ' +
                     value+'\n\n')
    return msg  # returns the test to be mailed to user


# sends emails
def process_email(message_content, receiver_add):
    try:
        sender_email_add = args.email_add
        password = args.password
        s = smtplib.SMTP(host='smtp.gmail.com.', port=587)
        s.starttls()
        s.login(sender_email_add, password)
        msg = MIMEMultipart()       # create a message
        msg['From'] = sender_email_add
        msg['To'] = receiver_add
        msg['Subject'] = "Details: About your Favourite TV Series is here"
        msg.attach(MIMEText(message_content, 'plain'))
        s.send_message(msg)
        print("mail send to ", receiver_add)
        del msg
        s.quit()
        print("email successfully send to {}".format(receiver_add))
    except Exception as e:
        #  print(e)
        print("Either the senders mail address or"
              " the password entered is wrong. Also check internet connection")


# performs database processing
def creating_database():
    # to ignore warnings given by MySQLdb
    filterwarnings('ignore', category=MySQLdb.Warning)
    try:
        conn = MySQLdb.connect(host="localhost", user=args.user,
                               password=args.passw)
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE IF NOT EXISTS IMDB')
        cursor.execute('USE IMDB')
        cursor.execute("CREATE TABLE IF NOT EXISTS SeriesList(Email_ADD "
                       "VARCHAR(100)NOT NULL UNIQUE, TvSeries VARCHAR(255))")
        return cursor, conn
    except Exception as e:
        #  print(e)
        print("could not connect to the database. Please "
              "chech Password/username")
        exit()


# Dumbs all data in the Database
def process_inputs():
    cursor, conn = creating_database()
    email_addresses = []
    response = 'y'
    while True and response == 'y':
        email_add = input("Enter your Email Address:\n")
        print("verifying email address....")
        if verify(email_add) is False:
            print("Entered Email Address is wrong")
            continue
        else:
            email_addresses.append(email_add)
            tvseries = update_tvseries_field(cursor, conn, email_add)
            if tvseries is not False:
                # create table
                try:
                    sql = ("INSERT INTO SeriesList (Email_ADD, TvSeries)"
                           "VALUES (%s, %s)")
                    val = (email_add, tvseries)
                    cursor.execute(sql, val)
                    conn.commit()
                except Exception as e:
                    #  print(e)
                    print("Problem with the database")
            else:
                pass
        while True:
            response = input("Enter y to enter next and n to stop:\n").lower()
            if response == 'y' or response == 'n':
                break
            else:
                print("wrong input")
    send_email(email_addresses, cursor)


# sends emails to email add that were added
def send_email(email_addresses, cursor):
    print("sending emails, takes time.....")
    for add in email_addresses:
        try:
            sql = "SELECT * FROM SeriesList WHERE Email_ADD = %s"
            val = (add,)
            cursor.execute(sql, val)
            data = cursor.fetchone()
            message_content = scrapping_imdb(data[1])
            process_email(message_content, add)
        except Exception as e:
            #  print(e)
            print("could not send email to {}", add)
    cursor.close()



# to update TvShows list
def update_tvseries_field(cursor, conn, email_add):
    sql = "SELECT * FROM SeriesList WHERE Email_ADD = %s"
    val = (email_add,)
    cursor.execute(sql, val)
    data = cursor.fetchone()
    # check if the user exists and provide option to update TvShows
    if data is not None:
        print("Your earlier TvSeries are :")
        print(data[1])
        while True:
            response = input("If want to add/delete "
                             "TvSeries press Y otherwise N:\n")
            if response.lower() == 'n':
                return False
            elif response.lower() == 'y':
                # update TvShows list and send the mail
                while True:
                    tvseries = input("Enter your series( comma seperated): "
                                     "Please be careful with the "
                                     "spellings:\n")
                    if len(tvseries) == 0:
                        print("Field can't be blank")
                    else:
                        sql = ("UPDATE SeriesList SET TvSeries = %s WHERE "
                               "Email_ADD = %s")
                        val = (tvseries, email_add)
                        cursor.execute(sql, val)
                        conn.commit()
                        return False
    else:
        # If the user does not exists
        return intake_tvseries()


if __name__ == '__main__':
    process_inputs()
