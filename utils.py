import pandas as pd
import time
from functools import wraps

def measure_time(func):
    """
    Decorator to measure and print the execution time of a function.
    
    Args:
        func (Callable): The function to measure.
        
    Returns:
        Callable: The wrapped function.
    """
    @wraps(func)
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

def track_row_changes(func):
    """
    Decorator to track how many rows are removed and how many rows are left
    in the DataFrame after the function is executed.
    """
    @wraps(func)  # Preserve the original function's metadata
    def wrapper(*args, **kwargs):
        # Find the DataFrame in the arguments (assumes it's the first argument)
        df = args[0] if isinstance(args[0], pd.DataFrame) else kwargs.get('df_dataset')
        if df is None:
            raise ValueError("The function must receive the DataFrame as the first positional argument or 'df_dataset' as a keyword argument.")

        initial_rows = len(df)
        result = func(*args, **kwargs)  # Call the original function
        final_rows = len(result)

        # Calculate changes
        removed_rows = initial_rows - final_rows

        # Print summary
        print(f"{func.__name__}: {removed_rows} rows removed, {final_rows} rows left.")

        return result  # Return the modified DataFrame
    return wrapper