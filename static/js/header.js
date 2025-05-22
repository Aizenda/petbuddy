const headerModel = {
	
}

const headerView = {
	element : {
		homeLogo:document.querySelector(".logo"),
		privateAdoption:document.querySelector("#privateAdoption"),
		publicAdoption:document.querySelector("#publicAdoption"),
		sendAdoption:document.querySelector("#sendAdoption"),
		loginButton:document.querySelector("#loginButton"),
		memberButton:document.querySelector("#memberButton") 
	}
}

const headerControl = {
	init(){
		headerView.element.homeLogo.addEventListener("click",()=>{
			this.goPath("/");
		});

		headerView.element.privateAdoption.addEventListener("click",()=>{
			this.goPath("/privateAdoption");
		})

		headerView.element.publicAdoption.addEventListener("click",()=>{
			this.goPath("/publicAdoption");
		})

		headerView.element.sendAdoption.addEventListener("click",()=>{
			this.goPath("/sendAdoption");
		})

		headerView.element.loginButton.addEventListener("click",()=>{
			this.goPath("/loginButton");
		})
	},

	goPath(url){
		location.href = url;
	}
}

document.addEventListener("DOMContentLoaded",()=>{
	headerControl.init();
});