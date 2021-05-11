
// ----------------STUDENT REGISTRATION SCRIPT ------------------------//
var department = document.getElementById('department_field');
var add_more = document.getElementById('add_more');
add_more.onclick = function(){
	var newfield = document.createElement('input');
	newfield.setAttribute('type','text');
	newfield.setAttribute('name','department');
	newfield.setAttribute('class','department');
	newfield.setAttribute('placeholder','another department');
	department.appendChild(newfield);
}

//-----------------ORGANISATION INSTRUCTOR---------------------//

function instAddToTable() {
    // First check if a <tbody> tag exists, add one if not
  if ($("#instTable tbody").length == 0) {
    $("#instTable").append("<tbody></tbody>");
  }

    // Append product to the table
  $("#instTable tbody").append(
    "<tr>" +
    "<td>"  "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" +
    "<button id='check-btn' type='button' onclick='approveInst(this);' class='btn btn-default'>" +
    "<i class='fa fa-check-circle' id='check' style='font-size:26px; color:green; margin-right: 60%'></i>"+ "</button>" +
    "<button id='times-btn' type='button' onclick='deleteInst(this);' class='btn btn-default'>" +
    "<i class='fa fa-times-circle' id='times' style='font-size:26px; color:red; margin-right:60%;'></i>"+ "</button>" +
    "</td>" +
    "</tr>");
}
function approveInst(ctl) {
    //code to delete the instructor;
}
function deleteInst(ctl) {
    //code to delete the instructor;
    alert('Are you sure you wish to delete Instructor with ID = ?');
}



//------------ ORGANISATION STUDENT ----------------------//

function stuAddToTable() {
    // First check if a <tbody> tag exists, add one if not
  if ($("#stuTable tbody").length == 0) {
    $("#stuTable").append("<tbody></tbody>");
  }

    // Append product to the table
  $("#stuTable tbody").append(
    "<tr>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" "</td>" +
    "<td>" +
    "<button type='button' id='check-btn' onclick='approveStu(this);' class='btn btn-default'>" +
    "<i class='fa fa-check-circle' id='check' style='font-size:26px; color:green; margin-right:90%;'></i>"+ "</button>" +
    "<button type='button' id='times-btn' onclick='deleteStu(this);' class='btn btn-default'>" +
    "<i class='fa fa-times-circle' id='times' style='font-size:26px; color:red; margin-right:20%;'></i>"+ "</button>" +
    "</td>" +
    "</tr>");
}
function approveStu(ctl) {
    //code to delete the instructor;
}
function deleteStu(ctl) {
    //code to delete the instructor;
    alert('Are you sure you wish to delete Instructor with ID = ?');
}

