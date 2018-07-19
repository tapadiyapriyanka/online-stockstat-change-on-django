from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
import pandas as pd
import numpy as np
import pika
import datetime
import os.path
from stockstats import StockDataFrame as sdf
import json
import csv
import sys
import shutil
import os
from matplotlib.figure import Figure
import io
import matplotlib.pyplot as plt, mpld3

# Create your views here.
def home(request):
    return HttpResponse("Hello World..!!")

class Customers(TemplateView):
    timer_id = None
    def get_graph(request):
        columns = ['Exchange','Token','Open_rate','Time1','Highest_rate','Lowest_price','Current_price','Close', 'Timestamp']
        
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, "CASHPrice1.csv")
        cashprice_data = pd.read_csv(file_path, sep=',', index_col=False, names=columns)
        
        file_path1 = os.path.join(module_dir, "Token.csv")
        token_csv = pd.read_csv(file_path1)
        
        cashprice_with_name = pd.merge(cashprice_data,token_csv[['Name','Token']], on='Token', how ="inner")
        
        cashprice_with_name = cashprice_with_name.drop('Token', 1)
        
        cashpriceN_with_stock = sdf.retype(cashprice_with_name)
        cashprice_with_name['rsi']=cashpriceN_with_stock['rsi_14']

        sample = cashpriceN_with_stock[['name','timestamp','open_rate_2_sma', 'open_rate']]
        print("columns of sample = ", sample.columns)
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel    = connection.channel()
        channel.exchange_declare(exchange='topic_logs',
                                 exchange_type='topic')
        result     = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        names = sample['name']
        # print(len(names))
        unique_names = []
        for name in names.unique():
            unique_names.append(name)
        
        binding_keys = '123'
        if not binding_keys:
                sys.stderr.write("Usage: %s [binding_keys]...\n" % sys.argv[0])
                sys.exit(1)

        channel.queue_bind(exchange='topic_logs',
                           queue=queue_name,
                           routing_key=binding_keys)
        def close_connec():
            channel.close()
            connection.close() 

        global timer_id
        timer_id = None

        def callback(ch, method, properties, body):
            global timer_id
            if timer_id is not None:
                ch.connection.remove_timeout(timer_id)

            raw_data = json.loads(body)   
            with open('/home/priyankat/Desktop/priyankat_data/Testing_folder/myopfile4.csv', 'a') as f:
                w = csv.writer(f)
                w.writerow(raw_data.values())  
                print("written to files ",raw_data.values())
            timer_id = ch.connection.add_timeout(2, close_connec)

        channel.basic_consume(callback,
                            queue=queue_name,
                            no_ack=True)
        channel.start_consuming()

        columns_new = ['open_rate', 'open_rate_2_sma', 'time']
        module_dir1 = os.path.dirname('/home/priyankat/Desktop/priyankat_data/Testing_folder/')
        file_path2 = os.path.join(module_dir1, "myopfile4.csv")
        stock_data = pd.read_csv(file_path2, sep=',', index_col=False, names=columns_new)

        stock_data['time'] = pd.to_datetime(stock_data['time'])
        stock_data['time_form'] = [datetime.datetime.time(d) for d in stock_data['time']]
        print(stock_data['time_form'])
        fig = plt.figure()
        ax = fig.add_subplot(111)
        stock_data.plot(x='time', y=['open_rate_2_sma', 'open_rate'],marker='o', ax=ax)    #ax=ax
        g = mpld3.fig_to_html(fig)
        return HttpResponse(g)

    # def simple(request):
    #     fig=Figure()
    #     ax=fig.add_subplot(111)
    #     ax.plot(range(10), range(10), '-')
    #     canvas=FigureCanvas(fig)
    #     response = HttpResponse(content_type='image/png')
    #     # fig.savefig(response, format='png')
        # canvas.print_png(response)
    #     return response

    def getimage(request):
        fig = plt.figure()
        plt.plot([1,2,3,4])
        g = mpld3.fig_to_html(fig)
        return HttpResponse(g)
