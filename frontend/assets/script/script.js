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