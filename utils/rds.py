"""
helper method for loading data from rds
"""
import os
import pymysql
import pandas as pd

meta = {
    "host": os.getenv('USER_SERVICE_HOST'),
    "user": os.getenv('USER_SERVICE_USER'),
    "password": os.getenv("USER_SERVICE_PASSWORD"),
    "port": int(os.getenv("USER_SERVICE_PORT")),
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    """
    get sql connection
    :return:
    """
    conn = pymysql.connect(**meta)
    return conn


def get_all_strategies(user_id):
    """
    get all strategies of a user
    :param user_id: current user
    :return: strategies in pd.dataframe
    """
    conn = get_connection()
    strategy_df = pd.read_sql(
        f"select * "
        f"from backtest.strategies  "
        f"where user_id = {user_id}",
        conn
    )
    return strategy_df


def get_all_backtests(user_id):
    """
    get all backtest results of a user
    :param user_id: current user
    :return: backtest results in pd.dataframe
    """
    conn = get_connection()

    backtest_df = pd.read_sql(
        f" SELECT s.strategy_name, s.strategy_id, b.backtest_id,"
        f" b.pnl_location, b.last_modified_date "
        f" FROM backtest.strategies s "
        f" LEFT JOIN backtest.backtests b ON s.strategy_id = b.strategy_id "
        f" WHERE s.user_id = {user_id} AND b.pnl_location is not null"
        f" ORDER BY b.last_modified_date;",
        conn
    )

    return backtest_df


def get_all_loations(strategy_ids):
    """
        get all backtest results of a user
        :param user_id: current user
        :return: backtest results in pd.dataframe
        """
    conn = get_connection()
    ids = "( " + " ".join(strategy_ids) + " )"

    backtest_df = pd.read_sql(
        f" SELECT s.strategy_name, b.pnl_location"
        f" FROM backtest.strategies s"
        f" LEFT JOIN backtest.backtests b ON s.strategy_id = b.strategy_id"
        f" WHERE b.strategy_id in {ids} AND b.pnl_location is not null"
        f" ORDER BY b.last_modified_date; ",
        conn
    )

    return backtest_df
