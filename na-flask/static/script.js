// var department = document.getElementById('department_field');
// var add_more = document.getElementById('add_more');
// add_more.onclick = function(){
// 	var newfield = document.createElement('input');
// 	newfield.setAttribute('type','text');
// 	newfield.setAttribute('name','department');
// 	newfield.setAttribute('id','department');
// 	newfield.setAttribute('class','department');
// 	newfield.setAttribute('placeholder','another department');
// 	department.appendChild(newfield);
// }

// var submit = document.getElementById('submit');
// submit.onclick = function (){
// 	var dept = document.getElementById('department').innerText;
// 	var names = [];
// 	names.push(dept);
// 	$.ajax({
//           type: "POST",
//           contentType: "application/json;charset=utf-8",
//           url: "/student-registration",
//           data: {'data': names}
//           });
// }

// $(document).ready(function boxes() {
// 	$('#submit').click(function() {
// 		var names = ['hat', 'cat']
// 	//  names.push($('#text').val());
// 	//  console.log(names);
// 		$.ajax({
//           type: "POST",
//           contentType: "application/json;charset=utf-8",
//           url: "/student-registration",
//           traditional: "true",
//           data: JSON.stringify({names}),
//           dataType: "json"
//           });
// 	});
// });

//-----------------ORGANISATION INSTRUCTOR---------------------//

// function instAddToTable() {
//     // First check if a <tbody> tag exists, add one if not
//   if ($("#instTable tbody").length == 0) {
//     $("#instTable").append("<tbody></tbody>");
//   }
//
//     // Append product to the table
//   $("#instTable tbody").append(
//     "<tr>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" +
//     "<button id='check-btn' type='button' onclick='approveInst(this);' class='btn btn-default'>" +
//     "<i class='fa fa-check-circle' id='check' style='font-size:26px; color:green; margin-right: 60%'></i>"+ "</button>" +
//     "<button id='times-btn' type='button' onclick='deleteInst(this);' class='btn btn-default'>" +
//     "<i class='fa fa-times-circle' id='times' style='font-size:26px; color:red; margin-right:60%;'></i>"+ "</button>" +
//     "</td>" +
//     "</tr>");
// }
// 
// function deleteInst(btn) {
//     //code to delete the instructor;
//     alert('Are you sure you wish to delete Instructor with ID = ?');
// }
//
//
//
// //------------ ORGANISATION STUDENT ----------------------//
//
// function stuAddToTable() {
//     // First check if a <tbody> tag exists, add one if not
//   if ($("#stuTable tbody").length == 0) {
//     $("#stuTable").append("<tbody></tbody>");
//   }
//
//     // Append product to the table
//   $("#stuTable tbody").append(
//     "<tr>" +
//     "<td>""</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" "</td>" +
//     "<td>" +
//     "<button type='button' id='check-btn' onclick='approveStu(this);' class='btn btn-default'>" +
//     "<i class='fa fa-check-circle' id='check' style='font-size:26px; color:green; margin-right:90%;'></i>"+ "</button>" +
//     "<button type='button' id='times-btn' onclick='deleteStu(this);' class='btn btn-default'>" +
//     "<i class='fa fa-times-circle' id='times' style='font-size:26px; color:red; margin-right:20%;'></i>"+ "</button>" +
//     "</td>" +
//     "</tr>");
// }
// function approveStu(btn) {
//     //code to delete the instructor;
//     var button = document.getElementById(btn.id);
//     button.disabled = true;
//     button.style.display = "none";
// }
// function deleteStu(btn) {
//     //code to delete the instructor;
//     alert('Are you sure you wish to delete Instructor with ID = ?');
// }

function approveBtn(btn) {
    var button = document.getElementById(btn.id);
    button.disabled = true;
    button.style.display = "none";

}