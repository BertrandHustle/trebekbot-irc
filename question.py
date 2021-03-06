import json
from random import randint

'''
Holds details about questions and questions themselves
:str text: The actual text of the question
:str answer: The answer to the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
'''

class Question:
    def __init__(self):
        jeopardy_json_file = open('./json_files/JEOPARDY_QUESTIONS1.json').read()
        question = json.loads(jeopardy_json_file)
        # json file has 216,930 questions
        question = question[randint(0, 216930)]
        self.text = question['question']
        self.value = Question.convert_value_to_int(question['value'])
        self.category = question['category']
        self.daily_double = Question.is_daily_double(self.value)
        self.answer = question['answer']

    def get_value(self):
        return ('$' + str(self.value))

    # to remove $ and commas from question values, e.g. '$2,500'
    @staticmethod
    def convert_value_to_int(value):
        try:
            # remove special characters if this is a string
            if type(value) == str:
                # check for negative numbers that haven't been converted to int yet
                if '-' in value:
                    return 0
                else:
                    value = ''.join(c for c in value if c.isalnum())
                    value = int(value)
            # check to make sure value is over $1
            if value < 1:
                return 0
            else:
                return value
        except (ValueError, TypeError) as error:
            return 0

    @staticmethod
    def is_daily_double(value):
        if type(value) is str:
            value = Question.convert_value_to_int(value)
        if value == 'Invalid Value':
            return False
        elif value < 1:
            return False
        elif value > 2000 and value % 100 != 0:
            return True
        else:
            return False
