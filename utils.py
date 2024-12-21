import pandas as pd
import time

def measure_time(func):
    """
    Decorator to measure and print the execution time of a function.
    
    Args:
        func (Callable): The function to measure.
        
    Returns:
        Callable: The wrapped function.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print(f"{func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper

def sort_df_by_list_order(df_, list_order, column_name):
    """
    Sort a DataFrame by the order of values in a list.

    Parameters:
    df (pd.DataFrame): The DataFrame to sort.
    list_order (list): A list of values specifying the desired order.
    column_name (str): The column in df to be sorted based on the list_order.

    Returns:
    pd.DataFrame: A new DataFrame sorted according to the list_order.
    """
    # Convert the specified column to a categorical type with the provided order
    df_[column_name] = pd.Categorical(df_[column_name], categories=list_order, ordered=True)
    # Sort the DataFrame by the specified column
    df_sorted = df_.sort_values(column_name).reset_index(drop=True)
    return df_sorted