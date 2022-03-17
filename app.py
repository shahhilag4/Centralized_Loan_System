import re

from flask import Flask, render_template, redirect, url_for, request, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
from datetime import datetime
import rstr
import os
import io
import requests
import base64
from imageio import imread, imwrite
import cv2 as cv


app = Flask(__name__)
app.secret_key = "@13@6$$#ddfccv"

#Connecting manager database

clientManager = "mongodb+srv://rajshukla1102:rajshukla1102@cluster0.eszou.mongodb.net/managerDb?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
clientClerk = "mongodb+srv://rajshukla1102:rajshukla1102@cluster0.eszou.mongodb.net/authentication?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"

#Connecting customer database

clientCustomer = "mongodb+srv://rajshukla1102:rajshukla1102@cluster0.eszou.mongodb.net/customerAuth?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
clientContact = "mongodb+srv://rajshukla1102:rajshukla1102@cluster0.eszou.mongodb.net/contact?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"

clientPublic = "mongodb+srv://rajshukla1102:rajshukla1102@cluster0.eszou.mongodb.net/public?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"




clusterManager = MongoClient(clientManager)
clusterClerk = MongoClient(clientClerk)
clusterCustomer = MongoClient(clientCustomer)
clusterContact = MongoClient(clientContact)
clusterPublic = MongoClient(clientPublic)

dbManager = clusterManager["managerDb"]
managerAuth = dbManager['managerAuth']

dbClerk = clusterClerk["authentication"]
clerk = dbClerk['clerk']

dbCustomer = clusterCustomer["customerAuth"]
customer = dbCustomer["customer"]
loanapp = dbCustomer["loanapplication"]

dbConatct = clusterContact["contact"]
contact = dbConatct["contactDetail"]
raiseissue = dbConatct["raiseissue"]
managerraiseissue = dbConatct["managerraiseissue"]

dbPublic = clusterPublic["public"]
adhar = dbPublic['adhar']

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")



def emi(amt,time,rate):
    r = rate/(12*100)
    emi = amt * r * ((1+r)**time)/((1+r)**time - 1)
    return emi

def getNextSequence(collection,name):
   return collection.find_and_modify(query= { '_id': name },update= { '$inc': {'seq': 1}}, new=True ).get('seq');

@app.route('/')
def main():
    return render_template('home/Home.html')

#This is end point for customer dashboard

@app.route('/customerhome')
def customerHome():
    if 'customer' in session:
        exist = customer.find_one({'email': session['customer']})
        # print(exist)
        clerkMess=raiseissue.find({'customerid':exist['customerid']})
        name = exist['name'].upper()
        customerid = exist['customerid']
        pan = exist['pan']
        amount=0
        emiAmount=0
        paidloan=0
        pendingloan=0
        user=loanapp.find({'customerid':exist['customerid']})

        files=[]

        for i in user:
            if(i['clerkapprove']=="Yes" and i['managerapprove']=="Yes"):
                amount=amount+float(i['amount'])
                emiAmount=emiAmount+float(i['monthlyEmi'])
                paidloan = paidloan + float(i['paidloan'])
                pendingloan = pendingloan + float(i['pendingloan'])
                files.append({
                    "bank": i['bank'].upper(),
                    "branch": i['branch'].upper(),
                    "loantype": i['loantype'].upper(),
                    "amount": i['amount'],
                    "emi": i['monthlyEmi'],
                    "pendingloan": i['pendingloan'],
                    "paidloan": i['paidloan'],
                })
        amount=round(amount,2)
        emiAmount=round(emiAmount,2)

        file=[]
        for i in clerkMess:
            file.append({
                "name": i['name'],
                "bank": i['bank'],
                'message': i['describe'],
                'issue': i['issue'],
                'loantype': i['loantype'],
                'describe': i['describe']
            })

        # print(file)


        return render_template('customer/DashboardHome.html', name=name, cid=customerid, pan=pan,amount=amount,emiAmount=emiAmount,paidloan=paidloan,pendingloan=pendingloan,files=files, wallet=exist['wallet'],file=file,totMessage=len(file))

    return redirect(url_for('customerLogin'))

#This is end point for customer registration

@app.route('/customerregister', methods=['POST', 'GET'])
def customerRegister():

    try:
        if request.method == 'POST':
            d, t = dt_string.split(' ')
            name = request.form['customerName']
            email = request.form['customerEmail']
            pan = request.form['pan']

            if(not name or not email):
                err = "Please fill required fields"
                return render_template('customer/CustomerRegister.html', err=err)
            else:

                # Registering for Customer

                exist = customer.find_one({'email': email})
                if exist is None:
                    hashpass = bcrypt.hashpw(
                        request.form['customerPass'].encode('utf-8'), bcrypt.gensalt())

                    customer_id = rstr.digits(10)

                    customer.insert_one({'customerid': customer_id, 'email': email, 'name': name,
                                    'pan': pan, 'date': d, 'password': hashpass,'wallet':int(0)})

                    session['customer'] = email

                    return render_template('customer/registrationsuccess.html', custid=customer_id)
                message = "user already exist"
                return render_template('customer/CustomerRegister.html', message=message)

    except:
        message = "Something messed up!! Please Register again"
        return render_template("customer/CustomerRegister.html", message=message)

    return render_template("customer/CustomerRegister.html")


@app.route('/customerlogin', methods=['GET', 'POST'])
def customerLogin():
    try:
        if request.method == 'POST':

            email = request.form['customerEmail']
            if(not email):
                err = "Please fill required fields"
                return render_template('customer/DashboardHome.html', err=err)
            else:

                userLogin = customer.find_one({'email': email})
                if userLogin:
                    if bcrypt.hashpw(request.form['customerPass'].encode('utf-8'), userLogin['password']) == userLogin['password']:
                        session['customer'] = email
                        return redirect(url_for('customerHome'))
                message = "invalid credentials"
                return render_template('customer/CustomerLogin.html', message=message)

    except:
        message = "Something messed up!!"
        return render_template("customer/CustomerLogin.html", message=message)

    return render_template("customer/CustomerLogin.html")

#This is end point for logout all users

@app.route("/logout")
def customerLogout():
    session.clear()
    return redirect(url_for('main'))


@app.route('/contactus', methods=['GET', 'POST'])
def contactForm():
    if request.method == 'POST':
        data = request.form
        name = data['name']
        email = data['email']
        message = data['message']
        mob = data['mob']
        contactFill = contact.find_one(
            {"name": name, "email": email, "message": message, "mob": mob})
        if contactFill != None:
            mess = "Message already sent!"
            return render_template("customer/ContactUs.html", mess=mess, name=name)
        contact.insert_one({"name": name, "email": email,
                           "message": message, "mob": mob})
        mess = "Thankyou for contacting us, We will reach out you soon..."
        return render_template("customer/ContactUs.html", mess=mess, name=name)

    return render_template("customer/ContactUs.html")

#This is end point for updating customer profile
#Like profile picture username.

@app.route('/customer-profile-update/<string:cid>')
def customerProfileHome(cid):
    if  'customer' in session:
        details = customer.find_one({'customerid': cid})
        clerkMess=raiseissue.find({'customerid':details['customerid']})
        file=[]
        for i in clerkMess:
            file.append({
                "name":i['name'],
                "bank":i['bank'],
                'message':i['describe'],
                'issue':i['issue'],
                'loantype':i['loantype'],
                'describe':i['describe']
            })
        return render_template("customer/CustomerProfileEdit.html", name=details['name'], phone=details['phone'],e=details['_id'],file=file,totMessage=len(file),cid=details['customerid'])
    return redirect(url_for('customerLogin'))


@app.route('/customerupdate/<string:id>', methods=['GET', 'POST'])
def customerProfile(id):

    if 'customer' in session:
        if request.method == 'POST':
            displayPic = request.files['displayPic']
            exist=customer.find_one({'email':session['customer']})

            name = request.form['customerName']
            phone = request.form['customerPhone']
            exist = customer.find_one({'_id': ObjectId(id)})
            customer.insert_one(
                {'name': name,'phone':phone, 'email': exist['email'], 'date': exist['date'], 'password': exist['password'],'customerid':exist['customerid'],'wallet':exist['wallet']})
            customer.delete_one({'_id': ObjectId(id)})

            file = displayPic.filename
            filename = file.split('.')
            filelength = len(filename)
            fileextension = filename[filelength-1]
            if(str(fileextension)=='pdf'):
                message="Upload only jpg/jpeg/png images"
                return render_template("customer/CustomerProfileEdit.html",name=exist['name'], email=exist['email'],e=exist['_id'],message=message)
            else:
                fileextension="jpg"

                displayPic.save(os.path.join("static/Profile/customer/",
                                         str(exist['customerid'])+'.'+str(fileextension)))

            # details = managerAuth.find_one({'username':session['user']})

                # return render_template("manager/ManagerProfileEdit.html",name=exist['name'], ifsc=exist['ifsc'],e=exist['_id'],username=exist['username'],message=message)
                return redirect(url_for('customerHome'))


        return render_template("customer/CustomerProfileEdit.html")
    return redirect(url_for('customerLogin'))



@app.route('/bankoption/<string:loanname>', methods=['POST', 'GET'])
def bankOption(loanname):
    if "customer" in session:
        return render_template('customer/BankOptions.html', loan=loanname)
    return redirect(url_for('main'))


@app.route('/loanoption')
def loanOption():
    if "customer" in session:
        return render_template('customer/LoanOptions.html')
    return redirect(url_for('main'))




@app.route('/loanform/<string:loanname>/<string:bankname>', methods=['POST', 'GET'])
def loanForm(loanname, bankname):
    if "customer" in session:
        return render_template('customer/LoanForm.html', loan=loanname, bank=bankname)
    return redirect(url_for('main'))


@app.route('/uploadfile', methods=['POST', 'GET'])
@app.route('/uploadfile/<string:loanname>/<string:bankname>', methods=['POST', 'GET'])
def uploadfile(loanname, bankname):
    if "customer" in session and request.method == 'POST':
        salary = request.files['file3']
        amount = request.form['amount']
        ifsc = request.form['ifsc'].upper()
        salaryname = str(salary.filename).split('.')
        time = request.form.get('time')

        if salaryname[len(salaryname) - 1] == 'pdf':

            URL = "https://ifsc.razorpay.com/"

            data = requests.get(URL + ifsc).json()

            if (data != "Not Found" and salary.filename):
                exist = customer.find_one({'email': session['customer']})
                cid = exist['customerid']
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                d, t = dt_string.split(' ')
                loanapp.insert_one(
                    {'customerid': cid, 'ifsc': ifsc, 'branch': data['BRANCH'].upper(), 'loantype': loanname.upper(), 'bank': bankname.upper(),
                     'amount': float(amount), 'clerkapprove': "No", 'managerapprove': "No", "date": d, 'time':int(time),'rate':8.65,'paidloan': float(0), 'pendingloan': 0,'pan':exist['pan']})


                file = salary.filename
                filename = file.split('.')
                filelength = len(filename)
                fileextension = filename[filelength - 1]
                salary.save(os.path.join("static/documents/salaryslip",
                                         str(cid) + '.' + str(fileextension)))

                # file = photograph.filename
                # filename = file.split('.')
                # filelength = len(filename)
                # fileextension = filename[filelength - 1]
                # photograph.save(os.path.join("static/documents/photo",
                #                              str(cid) + '.' + str(fileextension)))
                aadhardetail = adhar.find_one({'pan':exist['pan']})
                return render_template('camera.htm',aadhar = aadhardetail['ac'])
            message = "Upload all your files"
            if data == "Not Found":
                message = "Enter correct IFSC code"
            return render_template('customer/loanform.html', message1=message,loan=loanname, bank=bankname)
        return render_template('customer/loanform.html', message1="Upload all the files with given extension")
    return redirect(url_for('main'))


@app.route('/loanstatus')
def loanstatus():
    if "customer" in session:
        files = []
        cust = customer.find_one({'email': session['customer']})
        exist = loanapp.find({'customerid': cust['customerid']})
        clerkMess=raiseissue.find({'customerid':cust['customerid']})
        for x in exist:
            files.append({
                "bank": x['bank'].upper(),
                "branch": x['branch'].upper(),
                "loantype": x['loantype'].upper(),
                "amount": x['amount'],
                "date": x['date'],
                "clerkapprove": x['clerkapprove'].upper(),
                "managerapprove": x['managerapprove'].upper(),
            })
        file=[]
        for i in clerkMess:
            file.append({
                "name":i['name'],
                "bank":i['bank'],
                'message':i['describe'],
                'issue':i['issue'],
                'loantype':i['loantype'],
                'describe':i['describe']
            })

        # print(len(files))
        return render_template("customer/loanstatus.html", files=files,name=cust['name'],cid=cust['customerid'],file=file,totMessage=len(file))
    return redirect(url_for('main'))

@app.route('/payment')
def payment():
    if "customer" in session:
        return render_template("payments/Payment_Gateway.html")
    return redirect(url_for('main'))

@app.route('/checkout')
def checkout():
    if "customer" in session:
        return render_template("home/Receipt.html")
    return redirect(url_for('main'))

@app.route('/emicalci')
def emicalci():
    return render_template("home/emi.html")



############################################ Manager Panel ################################################


@app.route('/managerhome')
def managerHome():
    if 'user' in session:
        exist = managerAuth.find_one({'username': session['user']})
        name = exist['name']
        username = exist['username']
        user=loanapp.find({'ifsc':exist['ifsc']})
        count=0
        amount=0
        pending=0
        for i in user:
            if(i['managerapprove']=="Yes" and i['clerkapprove']=="Yes"):
                amount=amount+float(i['amount'])
            if(i['managerapprove']=='Yes'):
                count=count+1
            if(i['managerapprove']=='No'):
                pending=pending+1
        return render_template('manager/ManagerHome.html', name=name, username=username,branch=exist['address'],ifsc=exist['ifsc'],bank=exist['bank'],pending=(pending),amount=float(amount),count=count)
    return redirect(url_for('managerLogin'))


@app.route('/managerregister', methods=['POST', 'GET'])
def managerRegister():

    # try:
    if request.method == 'POST':
        d, t = dt_string.split(' ')
        name = request.form['managerName']
        userName = request.form['managerUser']
        ifsc = request.form['managerIfsc']
        URL = "https://ifsc.razorpay.com/"

        # Use get() method
        data = requests.get(URL + ifsc).json()

        if(not name or not userName or not ifsc):
            err = "Please fill required fields"
            return render_template('manager/ManagerRegister.html', err=err)
        else:

            # Registering for Bank Manager

            exist = managerAuth.find_one({'username': userName})
            if exist is None and data != "Not Found":
                hashpass = bcrypt.hashpw(
                    request.form['managerPass'].encode('utf-8'), bcrypt.gensalt())

                managerAuth.insert(
                    {'username': userName, 'name': name, 'bank': data['BANK'], 'address': data['ADDRESS'], 'ifsc': ifsc, 'date': d, 'time': t, 'password': hashpass})

                session['user'] = userName

                return redirect(url_for('managerLogin'))
            message = "user already exist"
            if(data == "Not Found"):
                message = "Enter correct IFSC Code"
            return render_template('manager/ManagerRegister.html', message=message)

    # except:
    #     message = "Something messed up!! Please Register again"
    #     return render_template("manager/ManagerRegister.html", message=message)

    return render_template("manager/ManagerRegister.html")


@app.route('/managerlogin', methods=['GET', 'POST'])
def managerLogin():
    try:
        if request.method == 'POST':
            userName = request.form['managerUser']
            if(not userName):
                err = "Please fill required fields"
                return render_template('manager/ManagerLogin.html', err=err)
            else:
                userLogin = managerAuth.find_one({'username': userName})

                if userLogin:
                    if bcrypt.hashpw(request.form['managerPass'].encode('utf-8'), userLogin['password']) == userLogin['password']:
                        session['user'] = userName
                        return redirect(url_for('managerHome'))
                message = "invalid credentials"
                return render_template('manager/ManagerLogin.html', message=message)

    except:
        message = "Something messed up!!"
        return render_template("manager/ManagerLogin.html", message=message)

    return render_template("manager/ManagerLogin.html")


@app.route('/profile-update/<string:username>')
def managerProfileHome(username):
    details = managerAuth.find_one({'username': username})

    return render_template("manager/ManagerProfileEdit.html", name=details['name'], ifsc=details['ifsc'],e=details['_id'],username=details['username'])


@app.route('/managerupdate/<string:id>', methods=['GET', 'POST'])
def managerProfile(id):


        if "user" in session and request.method == 'POST':
            displayPic = request.files['displayPic']
            name = request.form['managerName']
            ifsc = request.form['managerIfsc']
            exist = managerAuth.find_one({'_id': ObjectId(id)})
            managerAuth.delete_one({'_id': ObjectId(id)})
            managerAuth.insert_one(
                {'name': name, 'ifsc': ifsc, 'username': exist['username'], 'date': exist['date'], 'time': exist['time'], 'password': exist['password'],'address':exist['address'],'bank':exist['bank']})

            file = displayPic.filename
            filename = file.split('.')
            filelength = len(filename)
            fileextension = filename[filelength-1]
            if(str(fileextension)=='pdf'):
                message="Upload only jpg/jpeg/png images"
                return render_template("manager/ManagerProfileEdit.html",name=exist['name'], ifsc=exist['ifsc'],e=exist['_id'],username=exist['username'],message=message)
            else:
                fileextension="jpg"

                displayPic.save(os.path.join("static/Profile/manager",
                                         str(exist['username'])+'.'+str(fileextension)))
            # details = managerAuth.find_one({'username':session['user']})

                # return render_template("manager/ManagerProfileEdit.html",name=exist['name'], ifsc=exist['ifsc'],e=exist['_id'],username=exist['username'],message=message)
                return redirect(url_for('managerHome'))

    # except:
    #     message = "Something messed up!!"
    #     return render_template("manager/ManagerProfileEdit.html", message=message)

    # details = managerAuth.find_one({'username':session['user']})
        return render_template("manager/ManagerProfileEdit.html")


@app.route("/logout")
def managerLogout():
    session.clear()
    return redirect(url_for('main'))


@app.route('/clerkdetails/<string:condition>')
def clerkDetails(condition):
    if 'user' in session:
        manager = managerAuth.find_one({'username': session['user']})
        clerkD = clerk.find({'ifsc': manager['ifsc']})
        e = []
        if(condition=="pending"):
            for x in clerkD:
                if(x['approve']=="No"):
                        e.append({
                            "id": x["_id"],
                            "name": x['name'],
                            "phone": x['phone'],
                            "username": x['username'],
                            "date": x['date'],
                            "time": x['time'],
                            "approve": x['approve'],
                        })
            return render_template('manager/ClerkDetails.html', details=e,msg = "For Approval",name=manager['name'],username=manager['username'])
        else:
            for x in clerkD:
                if(x['approve']=="Yes"):
                        e.append({
                            "id": x["_id"],
                            "name": x['name'],
                            "phone": x['phone'],
                            "username": x['username'],
                            "date": x['date'],
                            "time": x['time'],
                            "approve": x['approve'],
                        })
            return render_template('manager/ClerkDetails.html', details=e,msg = "Approved",name=manager['name'],username=manager['username'])

    return redirect(url_for('managerLogin'))


@app.route('/approveclerk/<string:id>', methods=['GET', 'POST'])
def approveClerk(id):
    if 'user' in session:
        exist = clerk.find_one({'_id': ObjectId(id)})
        clerk.insert_one({'username': exist["username"], 'name': exist["name"], 'phone': exist["phone"],
                         'date': exist["date"], 'time': exist["time"], 'approve': 'Yes', 'password': exist['password'],'ifsc':exist['ifsc'],'bank':exist['bank'],'address':exist['address']})
        clerk.delete_one({'_id': ObjectId(id)})
        # return redirect(url_for('clerkDetails'))
        manager = managerAuth.find_one({'username': session['user']})
        clerkD = clerk.find({'ifsc': manager['ifsc']})
        e=[]
        for x in clerkD:
            if(x['approve']=="No"):
                    e.append({
                            "id": x["_id"],
                            "name": x['name'],
                            "phone": x['phone'],
                            "username": x['username'],
                            "date": x['date'],
                            "time": x['time'],
                            "approve": x['approve'],
                        })
        return render_template('manager/ClerkDetails.html', details=e,msg = "For Approval",name=manager['name'],username=manager['username'])
    return redirect(url_for('managerLogin'))


@app.route('/removeclerk/<string:id>', methods=['GET', 'POST'])
def removeClerk(id):
    if 'user' in session:
        clerk.delete_one({'_id': ObjectId(id)})
        # return redirect(url_for('clerkDetails'))
        manager = managerAuth.find_one({'username': session['user']})
        clerkD = clerk.find({'ifsc': manager['ifsc']})
        e=[]
        for x in clerkD:
            if(x['approve']=="No"):
                    e.append({
                            "id": x["_id"],
                            "name": x['name'],
                            "phone": x['phone'],
                            "username": x['username'],
                            "date": x['date'],
                            "time": x['time'],
                            "approve": x['approve'],
                        })
        return render_template('manager/ClerkDetails.html', details=e,msg = "For Approval",name=manager['name'],username=manager['username'])

    return redirect(url_for('managerLogin'))

@app.route('/managerverifycustomer/<string:condition>')
def managerverifycustomer(condition):
    if 'user' in session:
        managerdetail = managerAuth.find_one({'username': session['user']})
        customerdetail = loanapp.find({'ifsc': managerdetail['ifsc']})
        files = []
        # print(len(customerdetail))
        if(condition=="pending"):
            for x in customerdetail:
                if(x['clerkapprove'].upper() == "YES" and x['managerapprove'].upper() == "NO"):

                    files.append({
                        "loantype": x['loantype'].upper(),
                        "amount": x['amount'],
                        "time": x['time'],
                        "rate": x['rate'],
                        "date": x['date'],
                        "approve": x['managerapprove'].upper(),
                        "customerid": x['customerid'],
                        "ifsc": x['ifsc'],
                        "pan": x['pan'],
                    })
            return render_template('manager/FinalCustomerVerify.html', files=files, msg = "For Approval",username=managerdetail['username'],name=managerdetail['name'])
        else:
            for x in customerdetail:
                if (x['clerkapprove'].upper() == "YES" and x['managerapprove'].upper() == "YES"):

                    files.append({
                        "loantype": x['loantype'].upper(),
                        "amount": x['amount'],
                        "time": x['time'],
                        "rate": x['rate'],
                        "date": x['date'],
                        "approve": x['clerkapprove'].upper(),
                        "customerid":x['customerid'],
                        "ifsc": x['ifsc'],
                        "pan": x['pan'],
                    })
            return render_template('manager/FinalCustomerVerify.html', files=files, msg="Approved",username=managerdetail['username'],name=managerdetail['name'])
    return redirect(url_for('managerLogin'))



@app.route('/managerapprovecustomer/<string:cid>/<string:ifsc>/<string:loantype>')
def managerapprovecustomer(cid, ifsc, loantype):
    if 'user' in session:
        exist = loanapp.find_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})
        loanapp.insert_one(
            {'customerid': cid, 'ifsc': ifsc, 'branch': exist['branch'].upper(),'loantype': loantype.upper(), 'bank': exist['bank'],
             'amount': float(exist['amount']), 'time':exist['time'],'rate':exist['rate'],'clerkapprove': "Yes", 'managerapprove': "Yes", "date": exist['date'],'monthlyEmi':emi(int(exist['amount']),int(exist['time']),float(exist['rate'])),'paidloan':float(exist['paidloan']),'pendingloan':float(exist['amount']),'pan':exist['pan']})

        loanapp.delete_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})


        return redirect(url_for('managerverifycustomer',condition="pending"))
    return redirect(url_for('managerLogin'))


@app.route('/managerremovecustomer/<string:cid>/<string:ifsc>/<string:loantype>')
def managerremovecustomer(cid, ifsc, loantype):
    if 'user' in session:
        loanapp.find_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})
        return redirect(url_for('managerverifycustomer',condition="pending"))
    return redirect(url_for('managerLogin'))




@app.route('/track/<string:cid>')
def track(cid):
    if 'user' in session:
        exist = loanapp.find({'customerid':cid})
        files=[]
        manager = managerAuth.find_one({'username': session['user']})
        for x in exist:
            if (x['clerkapprove'].upper() == "YES" and x['managerapprove'].upper() == "YES"):
                files.append({
                    "loantype": x['loantype'].upper(),
                    "amount": x['amount'],
                    "time": x['time'],
                    "date": x['date'],
                    "pending": x['pendingloan'],
                    "bank": x['bank'].upper(),
                })
        return render_template("manager/Track.html",files=files,name=manager['name'],username=manager['username'])


    if 'clerk' in session:
        mngr = clerk.find_one({'username': session['clerk']})
        name = mngr['name']
        files = []
        exist = loanapp.find({'customerid': cid})
        for x in exist:
            if (x['clerkapprove'].upper() == "YES" and x['managerapprove'].upper() == "YES"):
                files.append({
                    "loantype": x['loantype'].upper(),
                    "amount": x['amount'],
                    "time": x['time'],
                    "date": x['date'],
                    "pending": x['pendingloan'],
                    "bank": x['bank'].upper(),
                })
        return render_template("clerk/Track.html", files=files, name=name,username=mngr['username'])
    return redirect(url_for('managerLogin'))


############################################# Clerk Reg.#############################
@app.route('/clerkhome')
def clerkHome():
    if 'clerk' in session:
        exist = clerk.find_one({'username': session['clerk']})
        name = exist['name']
        approve = exist['approve']
        # count=loanapp.find_one({'ifsc':exist['ifsc']})
        user=loanapp.find({'ifsc':exist['ifsc']})
        count=0
        amount=0
        pending=0
        for i in user:
            if(i['clerkapprove']=="Yes"):
                amount=amount+float(i['amount'])
            if(i['clerkapprove']=='Yes'):
                count=count+1
            if(i['clerkapprove']=='No'):
                pending=pending+1

        return render_template('clerk/DashboardHome.html', name=name, approve=approve,count=count,amount=amount,pending=pending,branch=exist['address'],ifsc=exist['ifsc'],bank=exist['bank'],username=exist['username'])
    return redirect(url_for('clerkLogin'))


@app.route('/clerkregister', methods=['POST', 'GET'])
def clerkRegister():
    if request.method == 'POST':
        try:
            approve = "No"
            d, t = dt_string.split(' ')

            name = request.form['clerkName']
            user = request.form['userName']
            phone = request.form['clerkMobile']
            ifsc = request.form['managerIfsc']

            URL = "https://ifsc.razorpay.com/"

            # Use get() method
            data = requests.get(URL + ifsc).json()

            if(not name or not user):
                err = "Please fill required fields"
                return render_template('clerk/ClerkRegister.html', err=err)
            else:

                # Registering for clerk
                exist = clerk.find_one({'username': user})
                if exist is None and data != "Not Found":
                    hashpass = bcrypt.hashpw(
                        request.form['clerkPass'].encode('utf-8'), bcrypt.gensalt())

                    clerk.insert_one({'username': user, 'name': name, 'phone': phone, 'bank': data['BANK'], 'address': data['ADDRESS'], 'ifsc': ifsc,
                                     'date': d, 'time': t, 'password': hashpass, 'approve': approve})
                    session['clerk'] = user
                    return redirect(url_for('clerkLogin'))
                message = "user already exist"
                if data == "Not Found":
                    message = "Enter Correct Ifsc Code "
                return render_template('clerk/ClerkRegister.html', message=message)

        except:
            message = "Something messed up!!"
            return render_template("clerk/ClerkRegister.html", message=message)

    return render_template("clerk/ClerkRegister.html")


@app.route('/clerklogin', methods=['GET', 'POST'])
def clerkLogin():
    try:
        if request.method == 'POST':

            email = request.form['clerkEmail']
            if(not email):
                err = "Please fill required fields"
                return render_template('clerk/ClerkLogin.html', err=err)
            else:

                userLogin = clerk.find_one({'username': email})
                if userLogin:
                    if bcrypt.hashpw(request.form['clerkPass'].encode('utf-8'), userLogin['password']) == userLogin['password']:
                        session['clerk'] = email
                        return redirect(url_for('clerkHome'))
                message = "invalid credentials"
                return render_template('clerk/ClerkLogin.html', message=message)

    except:
        message = "Something messed up!!"
        return render_template("clerk/ClerkLogin.html", message=message)

    return render_template("clerk/ClerkLogin.html")


@app.route("/logout")
def clerkLogout():
    session.clear()
    return redirect(url_for('main'))


@app.route('/clerkverifycustomer/<string:condition>')
def verifycustomer(condition):
    if 'clerk' in session:
        clerkdetail = clerk.find_one({'username': session['clerk']})
        customerdetail = loanapp.find({'ifsc': clerkdetail['ifsc']})
        files = []
        # print(len(customerdetail))
        if(condition=="pending"):
            for x in customerdetail:
                if x['clerkapprove'].upper() == "NO":

                    files.append({
                        "loantype": x['loantype'].upper(),
                        "amount": x['amount'],
                        "date": x['date'],
                        "approve": x['clerkapprove'].upper(),
                        "customerid": x['customerid'],
                        "time": x['time'],
                        "rate": x['rate'],
                        "pan": x['pan'],
                        "ifsc": x['ifsc'],
                    })
            return render_template('clerk/verifycustomer.html', files=files, msg = "For Approval",name=clerkdetail['name'],approve=clerkdetail['approve'],username=clerkdetail['username'])
        else:
            for x in customerdetail:
                if x['clerkapprove'].upper() == "YES":

                    files.append({
                        "loantype": x['loantype'].upper(),
                        "amount": x['amount'],
                        "date": x['date'],
                        "approve": x['clerkapprove'].upper(),
                        "customerid":x['customerid'],
                        "ifsc": x['ifsc'],
                         "time": x['time'],
                        "rate": x['rate'],
                        "pan": x['pan'],
                    })
            return render_template('clerk/verifycustomer.html', files=files, msg = "Approved",name=clerkdetail['name'],approve=clerkdetail['approve'],username=clerkdetail['username'])
    return redirect(url_for('clerkLogin'))

@app.route('/clerkapprovecustomer/<string:cid>/<string:ifsc>/<string:loantype>')
def clerkapprovecustomer(cid, ifsc, loantype):
    if 'clerk' in session:
        r=clerk.find_one({'username':session['clerk']})
        exist = loanapp.find_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})
        # print(exist)
        loanapp.delete_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})

        loanapp.insert_one(
            {'customerid': cid, 'ifsc': ifsc, 'branch': exist['branch'].upper(), 'loantype': loantype.upper(), 'bank': exist['bank'].upper(),
             'amount': float(exist['amount']), 'clerkapprove': "Yes", 'managerapprove': "No", "date": exist['date'],'time': exist['time'] ,'rate':exist['rate'],'paidloan':exist['paidloan'],'pendingloan':exist['pendingloan'],'pan':exist['pan']})
        return redirect(url_for('verifycustomer',condition="pending",approve=r['approve'],name=r['name'],username=r['username']))
    return redirect(url_for('clerkLogin'))



@app.route('/clerkremovecustomer/<string:cid>/<string:ifsc>/<string:loantype>')
def clerkremovecustomer(cid, ifsc, loantype):
    if 'clerk' in session:
        r=clerk.find_one({'username':session['clerk']})

        loanapp.delete_one({'customerid': cid,'ifsc':ifsc, 'loantype':loantype.upper()})


        return redirect(url_for('verifycustomer',condition="pending",approve=r['approve'],name=r['name'],username=r['username']))
    return redirect(url_for('clerkLogin'))

@app.route('/clerk-profile-update/<string:username>')
def clerkProfileHome(username):
    if  'clerk' in session:
        details = clerk.find_one({'username': username})

        return render_template("clerk/ClerkProfileEdit.html", name=details['name'], ifsc=details['ifsc'],e=details['_id'],username=details['username'])
    return redirect(url_for('clerkLogin'))


@app.route('/clerkupdate/<string:id>', methods=['GET', 'POST'])
def clerkProfile(id):

    if 'clerk' in session:
        if request.method == 'POST':
            displayPic = request.files['displayPic']
            name = request.form['clerkName']
            ifsc = request.form['clerkIfsc']
            exist = clerk.find_one({'_id': ObjectId(id)})
            clerk.delete_one({'_id': ObjectId(id)})
            clerk.insert_one(
                {'name': name, 'ifsc': ifsc, 'username': exist['username'], 'date': exist['date'], 'time': exist['time'], 'password': exist['password'],'address':exist['address'],'bank':exist['bank'],'phone':exist['phone'],'approve':exist['approve']})

            file = displayPic.filename
            filename = file.split('.')
            filelength = len(filename)
            fileextension = filename[filelength-1]
            if(str(fileextension)=='pdf'):
                message="Upload only jpg/jpeg/png images"
                return render_template("clerk/ClerkProfileEdit.html",name=exist['name'], ifsc=exist['ifsc'],e=exist['_id'],username=exist['username'],message=message)
            else:
                fileextension="jpg"

                displayPic.save(os.path.join("static/Profile/clerk/",
                                         str(exist['username'])+'.'+str(fileextension)))
            # details = managerAuth.find_one({'username':session['user']})

                # return render_template("manager/ManagerProfileEdit.html",name=exist['name'], ifsc=exist['ifsc'],e=exist['_id'],username=exist['username'],message=message)
                return redirect(url_for('clerkHome'))


        return render_template("clerk/ClerkProfileEdit.html")
    return redirect(url_for('clerkLogin'))

@app.route('/raiseissue/<string:cid>',methods=['GET', 'POST'])
def raiseIssue(cid):
    if 'clerk' in session:
        if request.method == 'POST':
            clerkdetail=clerk.find_one({'username':session['clerk']})
            customerdetail=loanapp.find_one({'customerid':cid})
            # print(customerdetail)
            describe=request.form['describe']
            issue=request.form.get('issue')
            raiseissue.insert_one({'describe':describe,'issue':issue,'customerid':customerdetail['customerid'],'loantype':customerdetail['loantype'],'name':clerkdetail['name'],'bank':customerdetail['bank']})
            return redirect(url_for('clerkHome'))
        return render_template('clerk/Documents.html')
    return redirect(url_for('clerkLogin'))

@app.route('/viewdocuments/<string:cid>/<string:pan>')
def viewdocuments(cid,pan):
    aadhardetail = adhar.find_one({'pan': pan}) #Here We Will Use Aadhaar Card API
    customerdetail = loanapp.find_one({'pan':pan})
    if 'clerk' in session :
        return render_template('clerk/Documents.html', file=cid, name=aadhardetail['name'], phone=aadhardetail['phone'],aadharno=aadhardetail['ac'], address=aadhardetail['address']
                               ,totalloan=customerdetail['amount'],totalpaid=customerdetail['paidloan'],totalpending=customerdetail['pendingloan'])
    if 'user' in session :
        return render_template('manager/Documents.html', file=cid, name=aadhardetail['name'], phone=aadhardetail['phone'],
                               aadharno=aadhardetail['ac'], address=aadhardetail['address']
                               , totalloan=customerdetail['amount'], totalpaid=customerdetail['paidloan'],
                               totalpending=customerdetail['pendingloan'])


    return redirect(url_for('clerkLogin'))

@app.route('/checkoutsuccess',methods=['GET', 'POST'])
def checkoutsuccess():
    if 'customer' in session:
        return render_template("home/Receipt.html",message = "Uploaded Successfully")
    return redirect(url_for('customerlogin'))

@app.route('/emicalculation',methods=['GET', 'POST'])
def emicalculation():
    import re
    if 'customer' in session:
        amount_text = request.form.get('price')
        print(amount_text)
        print(re.match("You have paid ₹(.+) amount", amount_text).group(1))
        amount = re.match("You have paid ₹(.+) amount", amount_text).group(1)
        print(amount)
        exist = customer.find_one({'email': session['customer']})
        print(exist)
        # customer.delete_one({'email': session['customer']})
        updated_amt = float(exist['wallet'])+float(amount)
        customer.update_one({'customerid': exist['customerid']}, {"$set": {"wallet": updated_amt}})
        #customer.insert_one({'customerid': exist['customerid'], 'email' : exist['email'], 'name': exist['name'],'phone': exist['phone'],'date': exist['date'], 'password': exist['password'],'wallet': float(exist['wallet'])+float(amount)})
    return {}

@app.route('/paynow/<string:cid>/<string:loantype>/<string:branch>', methods=['POST', 'GET'])
def paynow(cid,loantype,branch):
    if 'customer' in session:
        exist = loanapp.find_one({'customerid':cid,'loantype':loantype,'branch':branch})
        cust = customer.find_one({'customerid': cid})
        if(float(exist['monthlyEmi'])<=float(cust['wallet'])):
            customer.delete_one({'customerid': cid})
            customer.insert_one({'customerid': cust['customerid'], 'email': cust['email'], 'name': cust['name'],
                                 'phone': cust['phone'], 'date': cust['date'], 'password': cust['password'],'wallet': float(cust['wallet'])-float(exist['monthlyEmi'])})

            loanapp.delete_one({'customerid': cid, 'loantype': loantype, 'branch': branch})
            loanapp.insert_one(
                {'customerid': cid, 'ifsc': exist['ifsc'], 'branch': exist['branch'].upper(), 'loantype': loantype.upper(),
                 'bank': exist['bank'].upper(),
                 'amount': float(exist['amount']), 'clerkapprove': exist['clerkapprove'], 'managerapprove': exist['managerapprove'], "date": exist['date'], 'time': exist['time'],
                 'rate': 8.65, 'paidloan': float(exist['paidloan'])+float(exist['monthlyEmi']), 'pendingloan': float(exist['pendingloan'])-float(exist['monthlyEmi']),'monthlyEmi':float(exist['monthlyEmi']),'pan':exist['pan']})

        return redirect(url_for('customerHome'))

    return redirect(url_for('customerlogin'))

@app.route("/capture/<string:aadhar>",methods=['POST','GET'])
def capture(aadhar):
    if 'customer' in session:
        if request.method == 'POST':
            base64imagestr = request.form.get('image').split(',')[1]
            img = imread(io.BytesIO(base64.b64decode(base64imagestr)))
            print(img)
            path = "static/capture/"
            now = datetime.now()
            ctime = now.strftime("%H_%M_%S")
            # towrite.append(ctime)
            filename = path + aadhar + str(".jpg")
            print(filename)
            print(img.shape)
            image_to_write = cv.cvtColor(img, cv.COLOR_RGB2BGR)
            cv.imwrite(filename, image_to_write)

        return render_template("camera.htm")

    return redirect(url_for('customerlogin'))

@app.route('/success')
def success():
    return render_template("Page.html")

if __name__ == '__main__':
    app.run(port=5000, debug=True)


