function reset(){
  document.getElementById("value1").value = 0;
  document.getElementById("value2").value = 0;
  document.getElementById("value3").value = 0;
  
  document.getElementById("monthly-interest").innerHTML =" ₹ " +0;
  document.getElementById("monthly-payment").innerHTML =" ₹ " +0;
  document.getElementById("total-repayment").innerHTML =" ₹ " +0;
  document.getElementById("total-interest").innerHTML =" ₹ " +0;
}

function calculation(){
  
  var loanAmount = document.getElementById("value1").value;
  var interestRate = document.getElementById("value2").value;
  var loanDuration = document.getElementById("value3").value;
   
  var monthlyInterest = interestRate/(12*100);
  var monthlyPayment =  loanAmount * monthlyInterest * ((1+monthlyInterest)**loanDuration)/((1+monthlyInterest)**loanDuration - 1);
  var totalRepayment = (monthlyPayment * loanDuration);
  var monthly = (totalRepayment-loanAmount)/12;
  var totalInterestCost = totalRepayment-loanAmount;
  
   document.getElementById("monthly-interest").innerHTML = " ₹ " +monthly.toFixed(2);
  

  
   document.getElementById("monthly-payment").innerHTML = " ₹ " +monthlyPayment.toFixed(2); 
  
 
  
  document.getElementById("total-repayment").innerHTML =" ₹ " +totalRepayment.toFixed(2);
  

  
  document.getElementById("total-interest").innerHTML =" ₹ " +totalInterestCost.toFixed(2);
  
}