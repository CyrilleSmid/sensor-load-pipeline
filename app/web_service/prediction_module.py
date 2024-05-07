import dash_app.influx_query_manager as query_manager
from web_service import app, db
from web_service.models import User
import logging as log
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import tensorflow as tf
physical_device = tf.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_device[0], True)

from keras.models import Model
from keras.layers import Dense, LSTM, Dropout, Flatten, Input, concatenate
from tensorflow.keras.optimizers import Adam
import holidays
th_holidays = holidays.TH()
import datetime

dirname = os.path.dirname(__file__)
user_data_path = os.path.join(dirname, 'databases/user_data/')

PREDICTION_PERIOD=30
INITIAL_TRAINING_EPOCHS = 3000
TRAINING_EPOCHS = 1000


# Helper functions
def if_work_day(date): 
    if ((date in th_holidays) or (date.weekday()>=5)):
        return 0
    else: return 1
    
def reshape_ts_X(input_vector, time_steps, batch_size=None):
    x = np.lib.stride_tricks.sliding_window_view(input_vector[:-1], 
            window_shape=(time_steps, * input_vector.shape[1:]))
    x = x.reshape(-1, time_steps, * input_vector.shape[1:]) # removes extra dimension
    if (batch_size is not None) and (batch_size > 1):
        x = np.array_split(x, len(x) // batch_size)
    # else: x = x[np.newaxis, :, :] 
    return x

def reshape_ts_Y(target_vector, time_steps, batch_size=None):
    y = target_vector[time_steps:]
    if (batch_size is not None) and (batch_size > 1):
        y = np.array_split(y, len(y) // batch_size)
    # else: y = y[np.newaxis, :]
    return y

def compile_lstm():
    TIME_STEPS = 7
    INPUT_SHAPE = 2
    OUTPUT_SHAPE = 1
    # MODEL - LSTM
    input1 = Input(shape=(TIME_STEPS, INPUT_SHAPE))
    input2 = Input(shape=(1,))  

    lstm1 = LSTM(units=128, return_sequences=True)(input1)
    lstm1 = Dropout(0.2)(lstm1)

    lstm2 = LSTM(units=64, return_sequences=True)(lstm1)
    lstm2 = Dropout(0.2)(lstm2)

    lstm3 = LSTM(units=32, return_sequences=True)(lstm2)
    lstm3 = Dropout(0.2)(lstm3)

    lstm4 = LSTM(units=64, return_sequences=True)(lstm3)
    lstm4 = Dropout(0.2)(lstm4)

    lstm5 = LSTM(units=32, return_sequences=False)(lstm4)
    lstm5 = Dropout(0.2)(lstm5)

    fl_1 = Flatten()(lstm5)
    concatenated = concatenate([fl_1, input2])

    dense_1 = Dense(units=16)(concatenated)
    dense_2 = Dense(units=8)(dense_1)
    dense_3 = Dense(units=5)(dense_2)
    output = Dense(units=OUTPUT_SHAPE)(dense_3)

    model = Model(inputs=[input1, input2], outputs=output)

    model.compile(loss='mae', optimizer=Adam(), metrics=['mape'])
    return model
    
def prepare_data(df, scaler_path):
    total_load_df = df.sum(axis=1)
    
    data = total_load_df.reset_index()
    data.columns = ['Date', 'Total']
    data['If Work Day'] = data['Date'].map(if_work_day)
    X = data.iloc[:, 1:].to_numpy()
    next_if_work_day = data['If Work Day'].to_numpy().reshape(-1, 1)
    y = np.array(data[['Total']])

    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path) 
    elif total_load_df.shape[0] > 80:
        scaler = MinMaxScaler()
        scaler.fit(X)
        joblib.dump(scaler, scaler_path) 
        
    X_std = scaler.transform(X)
    X_std

    time_steps = 7

    X_batched_ts = reshape_ts_X(X_std, time_steps)
    next_if_work_day_ts = reshape_ts_Y(next_if_work_day, time_steps)
    y_batched_ts = reshape_ts_Y(y, time_steps)
    return (X_batched_ts,next_if_work_day_ts,y_batched_ts,scaler)

def train_model(X_batched_ts,next_if_work_day_ts,y_batched_ts, model, epochs):
    model.fit(
        x=[X_batched_ts, next_if_work_day_ts],
        y=y_batched_ts,
        epochs=epochs,
        verbose=0)
    return model

def predict_next(model, last_date, X_lagged_input, scaler, next_period = 7):
    next_if_work_day = list(map(if_work_day, [last_date + datetime.timedelta(days=x+1) for x in range(next_period)]))
    predictions = []
    for t_day in range(next_period):
        # Predict next day
        next_pred = model([np.expand_dims(X_lagged_input, axis=0), 
                            np.expand_dims(next_if_work_day[t_day], axis=0)]).numpy().tolist()
        predictions.append(next_pred)
        
        # Update input
        input_X = next_pred[0] + [next_if_work_day[t_day]]
        X_lagged_input = X_lagged_input[1:] + scaler.transform([input_X]).tolist()
    return predictions

def concat_with_replacement(df, new_df):
    indices_to_update = new_df.index.isin(df.index)

    df.loc[new_df.index[indices_to_update]] = new_df.loc[indices_to_update]

    concatenated_df = pd.concat([df, new_df[~indices_to_update]])
    return concatenated_df

def regular_model_update():
    with app.app_context():
        users = User.query.all()
        for user in users:          
            user_dir = os.path.join(user_data_path, f"user_{user.id}")
            os.makedirs(user_dir, exist_ok = True)
            
            user_daily_data_path = os.path.join(user_dir, "user_daily_data.csv")
            
            new_user_data = query_manager.get_all_after(start=0, client_id=f"client-{user.id}")
            if new_user_data.empty == False:
                new_user_data = query_manager.clean_up_influx_df(new_user_data).resample('D').sum()
            else: # No data in the database
                log.info(f"No data for user: {user.id}")
                continue
            try:
                cur_user_daily_data = pd.read_csv(user_daily_data_path)
            except FileNotFoundError:
                new_user_data.to_csv(user_daily_data_path)
            else: 
                cur_user_daily_data = cur_user_daily_data.set_index('Date')
                cur_user_daily_data.index = pd.to_datetime(cur_user_daily_data.index, format='%Y-%m-%d').tz_localize(None)
                
                if cur_user_daily_data.index[-1] == new_user_data.index[-1]:
                    log.info(f"No new data for user: {user.id}")
                else: # New data in the database
                    new_user_data.to_csv(user_daily_data_path)
                    cur_user_daily_data = new_user_data
                    log.info(f"Got new data for user: {user.id}. New shape: {cur_user_daily_data.shape}")
                    
                    user_model_path = os.path.join(user_dir, "lstm_model.h5")
                    user_scaler_path = os.path.join(user_dir, "c")
                    user_pred_path = os.path.join(user_dir, "user_predictions.csv")
                    if user.model_info.model_last_train_time is None:
                        if  cur_user_daily_data.shape[0] > 100:
                            model = compile_lstm()
                            user.model_info.model_train_status = f"Training initial model. Might take more than 5 minutes."
                            db.session.commit()
                            
                            for i in range(INITIAL_TRAINING_EPOCHS // 1000):
                                initial_training_data = cur_user_daily_data.iloc[:-((cur_user_daily_data.index[-1].weekday()+1) % 7), :] # Trim for clean weeks 
                                
                                X_batched_ts,next_if_work_day_ts,y_batched_ts, scaler = prepare_data(initial_training_data, scaler_path=user_scaler_path)
                                model = train_model(X_batched_ts,next_if_work_day_ts,y_batched_ts, 
                                                    model=model, epochs=800)
                                model.save(user_model_path)
                                user.model_info.model_train_status = f"Got preliminary results for epoch {(i+1) * 1000}/3000"
                                db.session.commit()
                                predictions=predict_next(model, initial_training_data.index[-1], X_batched_ts[-1].tolist(), scaler, next_period = PREDICTION_PERIOD)
                                pred_df = pd.DataFrame({'Prediction': np.array(predictions).sum(axis=2)[:, 0]})
                                pred_df['Date'] = [initial_training_data.index[-1] + datetime.timedelta(days=x+1) for x in range(PREDICTION_PERIOD)]
                                pred_df.to_csv(user_pred_path, index=False)
                                
                                cur_user_daily_data = query_manager.get_all_after(start=0, client_id=f"client-{user.id}")
                                cur_user_daily_data = query_manager.clean_up_influx_df(cur_user_daily_data).resample('D').sum()
                            
                            log.info(f"Finished training an initial model for user: {user.id}")
                            user.model_info.model_last_train_time = initial_training_data.index[-1].to_pydatetime()
                            user.model_info.model_train_status = f"Training complete. Predicted next {PREDICTION_PERIOD} days. Waiting for additional data."
                            db.session.commit()
                            
                        else:
                            log.info(f"Not enough data to initialized a model for user: {user.id}")
                            user.model_info.model_train_status = f"Not enough data to initialized a model {cur_user_daily_data.shape[0]} < 100 days"
                            db.session.commit()
                    else:
                        last_train_time = pd.Timestamp(user.model_info.model_last_train_time, tz=None)
                        log.info(f"Recovered last training time: {last_train_time}")
                        if cur_user_daily_data.index[-1] - last_train_time >= pd.Timedelta(1, "w"):
                            additional_data = cur_user_daily_data.loc[last_train_time - pd.Timedelta(3, "w"):, :]
                            new_training_data = additional_data.iloc[:-((additional_data.index[-1].weekday()+1) % 7), :] # Trim for clean weeks 
                            
                            model = compile_lstm()
                            try:
                                model.load_weights(user_model_path)
                            except ValueError:
                                log.warning(f"Failed to load model weights for user: {user.id}")
                            X_batched_ts,next_if_work_day_ts,y_batched_ts, scaler = prepare_data(new_training_data, scaler_path=user_scaler_path)
                            log.info(f"Started additional model training for user: {user.id} with {new_training_data.index[0]}-{new_training_data.index[-1]}")
                            user.model_info.model_train_status = f"Training model on new data"
                            db.session.commit()
                            
                            model = train_model(X_batched_ts,next_if_work_day_ts,y_batched_ts, 
                                                model=model, epochs=TRAINING_EPOCHS)
                            model.save(user_model_path)
                            log.info(f"Finished additional model training for user: {user.id}")
                            user.model_info.model_last_train_time = new_training_data.index[-1].to_pydatetime()
                            user.model_info.model_train_status = f"Training complete. Predicted next {PREDICTION_PERIOD} days. Waiting for additional data."
                            db.session.commit()
                            
                            pred_df = pd.read_csv(user_pred_path, parse_dates = ['Date']).set_index('Date')
                            
                            new_predictions=predict_next(model, new_training_data.index[-1], X_batched_ts[-1].tolist(), scaler, next_period = PREDICTION_PERIOD)
                            new_pred_df = pd.DataFrame({'Prediction': np.array(new_predictions).sum(axis=2)[:, 0]})
                            new_pred_df['Date'] = [new_training_data.index[-1] + datetime.timedelta(days=x+1) for x in range(PREDICTION_PERIOD)]
                            new_pred_df = new_pred_df.set_index('Date')
                            
                            pred_df = concat_with_replacement(pred_df, new_pred_df)
                            pred_df.to_csv(user_pred_path)
                            
                            
                            
                         
                        
                        
                        
                            
                        
                    
                
            
                
                    
                
                
                
                
            
            
            
            