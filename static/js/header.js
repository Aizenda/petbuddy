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
			this.checkToken(()=>this.goPath("/sendAdoption"));
			
		})

		headerView.element.loginButton.addEventListener("click",()=>{
			this.goPath("/login");
		})

		headerView.element.memberButton.addEventListener("click",()=>{
			this.goPath("/member");
		})
	},

	goPath(url){
		window.location.href = url;
	},

	checkToken(callback){
		const token = localStorage.getItem("token");
		if(!token || token===null){
			alert("請登入");
			window.location.href = "/login";
			return;
		};
		callback();
	}
}

document.addEventListener("DOMContentLoaded",()=>{
	headerControl.init();
});