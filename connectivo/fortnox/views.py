from django.shortcuts import render,get_object_or_404,redirect
from django.urls import reverse_lazy,reverse
from django.http import HttpResponseRedirect
from django.views import generic
from . import models
from django.contrib import messages

import os
import logging


import requests
import recurly
import json

recurly.SUBDOMAIN = 'connectivo'
recurly.API_KEY = 'edf04f55c7004393adb1e53fbae7bb42'

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging_dir = os.path.join(BASE_DIR,"logs","error_logging.log")
log_format = "%(asctime)s::%(levelname)s::%(name)s::%(filename)s::%(lineno)d::%(message)s"
logging.basicConfig(filename=logging_dir,format=log_format,filemode="w")





################################################################
###### this function handles the actual fortnox api calls#######
###############################################################
def fortnox_api_call(http_method,endpoint,data):
    try:
        r = http_method(
            url="https://api.fortnox.se/3/"+endpoint,
            headers = {
                        "Access-Token":"f895dac6-9b6a-4885-8daa-2041512f0911",
                        "Client-Secret":"I56Jh4yJSU",
                        "Content-Type":"application/json",
                        "Accept":"application/json",
                     },
            data = json.dumps(data)
                     )
        # print('Response HTTP Status Code : {status_code}'.format(status_code=r.status_code))
        return r
    except requests.exceptions.RequestException as e:
        # print('HTTP Request failed')
        logger=logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.error(e)
####################################################################



# Create your views here.

######### the index page ##############
class indexView(generic.TemplateView):
    template_name="index.html"
######################################




#########################################################################
###### this view handles syncing fortnox account with recurly ###########
########################################################################
def sync_view(request):

    if request.method != "POST":

        def get_recurly_paid_invoices():
            try:
                return recurly.Invoice.all_paid(order='asc')
            except Exception as e:
                # print('HTTP Request failed')
                logger=logging.getLogger()
                logger.setLevel(logging.DEBUG)
                logger.error(e)


         # gets a dictionary of fortnox customer accounts
        def get_fortnox_customer_dict():
            r = fortnox_api_call(http_method=requests.get,endpoint='customers',data={})

            if r != None:
                customers_dict = json.loads(r.content)["Customers"]
                return customers_dict
            else:
                return r

        # gets a dictionary of fortnox articles
        def get_fortnox_articles_dict():
            r = fortnox_api_call(http_method=requests.get,endpoint='articles',data={})

            if r != None:
                articles_dict = json.loads(r.content)["Articles"]
                return articles_dict
            else:
                return r


        # creates a fortnox customer account
        def create_fortnox_customer_account(name):
            data = {
            "Customer": {
                "Name": name
                }
            }
            r = fortnox_api_call(http_method=requests.post,endpoint='customers',data=data)
            if r != None:
                return json.loads(r.content)["Customer"]["CustomerNumber"]
            else:
                return r


        # creates a fortnox article
        def create_fortnox_article(plan):
            data = {
            "Article": {
                 "Description":plan.name,
                # "ArticleNumber":str(int(plan.plan_code)+103),
                # "DirectCost":plan.unit_amount_in_cents,
                }
            }

            r = fortnox_api_call(http_method=requests.post,endpoint='articles',data=data)
            return r



        # creates a fortnox invoice
        def send_to_fortnox(invoice,plan,customer_number):

            data = {
                "Invoice": {
                "Currency":invoice.currency,
                     "InvoiceRows":[{
                        "ArticleNumber":plan.plan_code,
                        "Discount": invoice.discount_in_cents,
                        "Price": invoice.subtotal_in_cents,
                        "Unit": invoice.currency,
                     }],
                    "CustomerNumber": customer_number,
                    # "DueDate":invoice.attempt_next_collection_at,
                    # "InvoiceDate":invoice.created_at,
                    "TermsOfPayment":invoice.terms_and_conditions,
                    "Total":invoice.total_in_cents,
                    }
                }

            r = fortnox_api_call(http_method=requests.post,endpoint='invoices',data=data)

            return r

        # handles the syncing of fortnox and recurly accounts
        def sync_recurly_fortnox(last_synced):
            begin_sync = False
            # print(get_fortnox_articles_dict())
            fortnox_customer_dict = get_fortnox_customer_dict()

            recurly_paid_invoices = get_recurly_paid_invoices()

            for invoice in recurly_paid_invoices:

                if begin_sync == True:
                    account_exists_flag = False

                    recurly_customer_account = invoice.account()
                    subscriptions_pages = invoice.subscriptions()

                    for subscription in subscriptions_pages:
                        # print("this is the plan code: "+subscription.plan.plan_code)
                        try:
                            response = create_fortnox_article(subscription.plan)
                        except:
                            pass

                    for fortnox_customer in fortnox_customer_dict:
                        if fortnox_customer["Name"] == recurly_customer_account.first_name+" "+recurly_customer_account.last_name:
                            account_exists_flag = True

                    if account_exists_flag == True:
                            # print("customer already exits")
                            response = send_to_fortnox(invoice=invoice,plan=subscription.plan,customer_number = fortnox_customer["CustomerNumber"])
                    else:
                        customer_number = create_fortnox_customer_account(recurly_customer_account.first_name+" "+recurly_customer_account.last_name)
                        response = send_to_fortnox(invoice=invoice,plan=subscription.plan,customer_number=customer_number)

                if last_synced == None:
                    begin_sync=True
                elif invoice.invoice_number == last_synced.document_number:
                    begin_sync = True

                if invoice == recurly_paid_invoices[len(recurly_paid_invoices)-1]:
                    return invoice



        # this is the main sync_view function. it is not get_queryset() class method!
        def queryset():
            try:
                last_synced =  models.lastSyncedRecord.objects.all()
                if len(last_synced) > 0:
                    new_last_synced = sync_recurly_fortnox(last_synced=last_synced[0])
                    last_synced[0].document_number = new_last_synced.invoice_number
                    last_synced[0].save()
                else:
                    new_last_synced = sync_recurly_fortnox(last_synced=None)
                    models.lastSyncedRecord.objects.create(document_number = new_last_synced.invoice_number)
                messages.success(request, 'Synchronization completed! Your fortnox invoice database is up to date')
            except Exception as e:
                logger=logging.getLogger()
                logger.setLevel(logging.DEBUG)
                logger.error(e)

        queryset()
        return HttpResponseRedirect(reverse_lazy("fortnox:index"))




def post_article_view(request):
    if request.method == "POST":
        data = {
            "Article": {
                 "Description":request.POST.get("description"),
                # "ArticleNumber":str(int(plan.plan_code)+103),
                # "DirectCost":plan.unit_amount_in_cents,
            }
        }

        r = fortnox_api_call(http_method=requests.post,endpoint='articles',data=data)
        try:
            if r != None:
                if (str(r.status_code))[0] == "2":
                    messages.success(request, 'your article was created successfully! go to "All articles" to see all your articles')
                else:
                    messages.error(request, "unfortunately, for some reason, your article couldn't be created. please try again later")
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return HttpResponseRedirect(reverse_lazy("fortnox:index"))
    else:
        return render(request,'post_article.html')




def update_article_view(request,**kwargs):
    if request.method == "POST":
        data = {
            "Article": {
                 "Description":request.POST.get("description"),
                # "ArticleNumber":str(int(plan.plan_code)+103),
                # "DirectCost":plan.unit_amount_in_cents,
            }
        }

        r = fortnox_api_call(http_method=requests.put,endpoint="articles/"+request.POST.get("article_number"),data=data)

        try:
            if (str(r.status_code))[0] == "2":
                messages.success(request, 'your article was updated successfully! go to "All articles" to see all your articles')
            else:
                messages.error(request, "unfortunately, for some reason, your article couldn't be updated. please try again later")
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)


        return HttpResponseRedirect(reverse_lazy("fortnox:index"))

    elif kwargs.get("article_number"):#when the update article is coming from the view_articles page
        return render(request,'update_article.html',{"article_number":kwargs.get("article_number")})
    else:
        return render(request,"update_article.html",{"article_number":None})


def create_invoice_view(request):
    if request.method == "POST":
        data = {
        "Invoice": {
        "Currency":request.POST.get('currency'),
             "InvoiceRows":[{
                "ArticleNumber":request.POST.get('article_number'),
                "Discount": request.POST.get('discount'),
                "Price": request.POST.get('price'),
                "Unit": request.POST.get('unit'),
             }],
            "CustomerNumber": request.POST.get('customer_number'),
            "DueDate":request.POST.get('due_date'),
            "InvoiceDate":request.POST.get('invoice_date'),
            # "TermsOfPayment":request.POST.get('terms_of_payment'),
            # "Total":request.POST.get('total')"
            }
        }

        r = fortnox_api_call(http_method=requests.post,endpoint="invoices",data=data)

        try:
            if (str(r.status_code))[0] == "2":
                messages.success(request, 'your invoice was created successfully! go to "View invoices" to see all your invoices')
            else:
                messages.error(request, 'an error occurred. please check the information you are submitting')
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return HttpResponseRedirect(reverse_lazy("fortnox:index"))
    else:
        return render(request,'create_invoice.html')



def bookkeep_invoice_view(request,**kwargs):
    if request.method == "POST":
        r = fortnox_api_call(http_method=requests.put,endpoint="invoices/"+request.POST.get("document_number")+"/bookkeep",data={})

        try:
            if (str(r.status_code))[0] == "2":
                messages.success(request, 'your invoice was booked successfully! go to "View invoices" to see all your invoices')
            else:
                messages.error(request, 'an error occurred. This invoice may have been booked already. please check the information you are submitting. Note, you can only book an invoice you created yourself')
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return HttpResponseRedirect(reverse_lazy("fortnox:index"))

    elif kwargs.get("document_number"):
        r = fortnox_api_call(http_method=requests.put,endpoint="invoices/"+kwargs.get("document_number")+"/bookkeep",data={})

        try:
            if (str(r.status_code))[0] == "2":
                messages.success(request, 'your invoice was booked successfully! go to "View invoices" to see all your invoices')
            else:
                messages.error(request, 'an error occurred. This invoice may have been booked already. please check the information you are submitting. Note, you can only book an invoice you created yourself')
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return HttpResponseRedirect(reverse_lazy("fortnox:index"))

    else:
        return render(request,'bookkeep_invoice.html')



def invoices_view(request,**kwargs):
    if request.method == "GET":
        r = fortnox_api_call(http_method=requests.get,endpoint="invoices/?page="+kwargs.get("page"),data={})
        try:
            invoices = json.loads(r.content)["Invoices"]
            page_count = json.loads(r.content)["MetaInformation"]["@TotalPages"]
            pages = []
            for i in range(1,page_count+1):
                pages.append(i)
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return render(request,'view_invoices.html',{"invoices":invoices,"pages":pages})

def articles_view(request,**kwargs):
    if request.method == "GET":
        r = fortnox_api_call(http_method=requests.get,endpoint="articles/?page="+kwargs.get("page"),data={})

        try:
            # print(r.content)
            articles = json.loads(r.content)["Articles"]
            page_count = json.loads(r.content)["MetaInformation"]["@TotalPages"]
            pages = []
            for i in range(1,page_count+1):
                pages.append(i)
        except Exception as e:
            # print('HTTP Request failed')
            logger=logging.getLogger()
            logger.setLevel(logging.DEBUG)
            logger.error(e)

        return render(request,'view_articles.html',{"articles":articles,"pages":pages})

def last_synced_invoice_view(request):
    if request.method == "GET":
        last_synced_invoice  =  models.lastSyncedRecord.objects.all()
        if len(last_synced_invoice) > 0:
            try:
                r = fortnox_api_call(http_method=requests.get,endpoint="invoices/"+last_synced_invoice[0].document_number,data={})
                invoice = json.loads(r.content)["Invoice"]
            except Exception as e:
                invoice = None
                # print('HTTP Request failed')
                logger=logging.getLogger()
                logger.setLevel(logging.DEBUG)
                logger.error(e)

            return render(request,"last_synced_invoice.html",{"invoice":invoice})
        else:
            return render(request,"last_synced_invoice.html",{"invoice":None})
