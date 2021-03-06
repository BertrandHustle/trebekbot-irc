import pytest
import host
import question
import db
import slackclient
from re import findall
from os import remove
from main import slack_token

# set up test objects
sc = slackclient.SlackClient(slack_token)
test_question = question.Question()
test_host = host.Host(sc)
test_db = db.db('test.db')

# fixture for tearing down test database completely
@pytest.fixture
def db_after():
    yield db_after
    test_db.drop_table_users(test_db.connection)

# fixture for cleaning out test users from database (but leaving table present)
@pytest.fixture
def scrub_test_users():
    yield scrub_test_users
    test_db.connection.execute(
    '''
    DELETE FROM USERS
    '''
    )

# set up fixture to populate test db with a range of scorers
@pytest.fixture
def populate_db():
    test_users = ['Bob', 'Jim', 'Carol', 'Eve', 'Morp']
    test_score = 101
    # ensure that we have a varied list of scorers
    for user in test_users:
        test_db.add_user_to_db(test_db.connection, user)
        test_db.update_score(test_db.connection, user, test_score)
        test_score += 100
    # check to make sure negative numbers work too
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (-156, 'Eve')
    )

# tests question constructor
def test_question_constructor():
    assert type(test_question.answer) == str
    assert type(test_question.category) == str
    assert type(test_question.daily_double) == bool
    assert type(test_question.text) == str
    assert type(test_question.value) == int

def test_get_value():
    '''
    we want to make sure that it's a valid Jeopardy point value,
    so it has to be in an increment of $100
    '''
    value_no_dollar_sign = test_question.get_value()[2:]
    assert int(value_no_dollar_sign) % 100 == 0

@pytest.mark.parametrize("test_value, expected_value", [
 ('$100', False),
 ('$5578', True),
 (200, False),
 (10239, True),
 (1, False),
 (-1, False),
 (0, False),
 ('0', False)
])
def test_is_daily_double(test_value, expected_value):
    assert test_question.is_daily_double(test_value) == expected_value

@pytest.mark.parametrize("test_value, expected_value", [
 ('$2,500', 2500),
 ('asjdjasdj', 0),
 (0, 0),
 (-1, 0),
 (-888, 0),
 ('-$4,001', 0),
 (None, 0)
])
def test_convert_value_to_int(test_value, expected_value):
    assert test_question.convert_value_to_int(test_value) == expected_value

@pytest.mark.parametrize("test_value, expected_value", [
 ('Hall & Oates', 'halloates'),
 ('Hall and Oates', 'halloates'),
 ('Androgynous', 'androgynous'),
 ('Hall & Oates\'s Oats and Halls', 'halloatessoatshalls')
])
def test_strip_answer(test_value, expected_value):
    assert test_host.strip_answer(test_value) == expected_value

@pytest.mark.parametrize("given_answer, expected_answer, expected_value", [
 ('Bath', 'Borth', False),
 ('Bath', 'beth', False),
 (600, 'Borth', False),
 (None, 'Borth', False),
 ('mary queen of scotts','Mary, Queen of Scots', True),
 ('','Mary, Queen of Scots', False),
 ('MAAAARYYYY QUEEN OF SCOOOOOOTTSSS','Mary, Queen of Scots', False),
 ('borp', 'Henry James', False),
 ('bagpipe', 'a bagpipe', True),
 ('infintesimal', 'infinitesimal', True),
 ('infiniitesimal', 'infinitesimal', True),
 ('amber alert', 'an Amber alert', True),
 ('the good Samaritan', 'The Good Samaritan', True),
 ('it’s a wonderful life', 'It\'s A Wonderful Life', True),
 ('Hall and Oates', 'Hall & Oates', True),
 ('comedy of errors', 'The Comedy of Errors', True)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert test_host.fuzz_answer(given_answer, expected_answer) == expected_value

# TODO: rewrite database tests using Mock
# TODO: add bad values in here e.g. ' ', 0
def test_add_user_to_db():
    # do this twice to ensure that we're adhering to the UNIQUE constraint
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_query = test_db.connection.execute(
    '''
    SELECT * FROM USERS WHERE NAME = ?
    ''',
    ('Bob',)
    )
    query_results = test_query.fetchall()
    print(query_results)
    check_results = findall(r'Bob', str(query_results))
    # asserts both that Bob was added and that he was only added once
    assert len(check_results) == 1

# TODO: test to make sure a new user gets their score updated on first answer
# TODO: test to make sure lower limit of -$10000 works
@pytest.mark.parametrize("user, value_change, expected_result", [
 ('LaVar', '0', 0),
 ('LaVar', '-200', -200),
 ('LaVar', '-200', -400),
 ('Stemp', 'Invalid Value', 0),
 ('boop', '-9000', -9000),
 ('boop', '-500', -9500)
 # TODO: add more exceptions here
 # ('LaVar', 'ants', False)
])
def test_update_score(user, value_change, expected_result):
    test_db.add_user_to_db(test_db.connection, user)
    test_db.update_score(test_db.connection, user, value_change)
    assert test_db.return_score(test_db.connection, user) == expected_result
'''
redundant, but making sure the test itself
was working properly w/parametrization
'''
def test_test_update_score(scrub_test_users):
    test_db.add_user_to_db(test_db.connection, 'test')
    test_db.update_score(test_db.connection, 'test', '500')
    assert test_db.return_score(test_db.connection, 'test') == 500
    test_db.update_score(test_db.connection, 'test', '-5000')
    assert test_db.return_score(test_db.connection, 'test') == -4500
    test_db.update_score(test_db.connection, 'test', '-100000')
    assert test_db.return_score(test_db.connection, 'test') == -4500

def test_return_top_ten(populate_db, scrub_test_users):
    expected_list = [
    (5, 'Morp', 501),
    (3, 'Carol', 301),
    (2, 'Jim', 201),
    (1, 'Bob', 101),
    (4, 'Eve', -156)
    ]
    assert test_db.return_top_ten(test_db.connection) == expected_list

# TODO: test if user doesn't exist
def test_return_score(db_after):
    test_db.add_user_to_db(test_db.connection, 'Lucy')
    assert test_db.return_score(test_db.connection, 'Lucy') == 0
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (100, 'Lucy')
    )
    assert test_db.return_score(test_db.connection, 'Lucy') == 100
