# Main file for trebekbot
# loosely based on this tutorial: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
import host
import db
import question
from slackclient import SlackClient
from math import ceil

author = 'bertrand_hustle'
bot_name = 'trebekbot'

# retrieve id/token/etc. from env variables
bot_id = os.environ.get('TREBEKBOT_ID')
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = SlackClient(slack_token)
channel = '#trivia'
# this needs to be outside the loop so it stays persistant

question_asked = None
answer_given = None
# timeout for questions
timer = 0

#TODO: impliment timeout on questions
if __name__=='__main__':
    # create host object
    host = host.Host(slack_client)
    # setup database
    user_db = db.db('users.db')
    user_db.create_table_users(user_db.connection)
    # host introduces itself to channel
    host.say(channel, host.help_text)

    while True:
        # time loops for debug purposes
        loop_start_time = time.time()
        # get rolling slack output
        slack_output = slack_client.rtm_read()
        # main functions
        host.hello(slack_output)
        host.help(slack_output)
        host.myscore(slack_output, user_db)
        host.top_ten(slack_output)

        # this is how we store a persistant question/answer
        current_question = host.ask_question(slack_output)
        if current_question:
            question_asked = current_question
            '''
            if question.Question.is_daily_double(current_question):
                host.say(channel, 'It\s a DAILY DOUBLE')
                # TODO: fully impliment scoring here
            '''
        current_answer = None
        if host.hear(slack_output, 'whatis'):
            current_answer = host.hear(slack_output, 'whatis')
        if current_answer:
            answer_given = current_answer

        # logic for getting and checking question answers
        if question_asked and answer_given:
            host.check_answer(slack_output, question_asked)
            # user_db.add_user_to_db(user_db.connection, user_that_answered_question)
            question_asked = None
            answer_given = None

        # having an answer_given stored without a question can lead to
        # trebekbot becoming unable to be asked questions, so we need
        # to make sure that if there's an answer stored without a question,
        # we wipe them both

        elif answer_given:
            question_asked = None
            answer_given = None
        else:
            pass

        # timeout mechanism
        if question_asked:
            timer += 1
        if timer >= 120:
            host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
            question_asked = None
            answer_given = None
            timer = 0
        if not question_asked and not answer_given:
            timer = 0

        # printing for debug purposes
        print(slack_output)
        if question_asked:
            print(question_asked.text)
        print('GIVEN ANSWER')
        print(answer_given)
        print('========================================')
        print(timer)
        # track time per loop for debugging
        print(round(time.time()-loop_start_time, 5))
        # delay so trebekbot has time to think
        time.sleep(1)
