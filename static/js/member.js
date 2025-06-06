const memberModel = {
	async getUser(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/user",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	},
	async advertise_for_adoption(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/advertise_for_adoption",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	},
	async want_to_adopt(){
		const token = localStorage.getItem("token");
		try{
			const req = await fetch("/api/want_to_adopt",{
				method:"GET",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				}
			});

			const data = await req.json();

			if(!data.ok){
				throw new Error(data.message)
			}
			
			return data;

		}catch(e){
			console.log(e);
			return e;
		}
	}
}

const memberView = {
	element:{
		name:document.getElementById("name"),
		time:document.getElementById("time"),
		adoption:document.getElementById("adoption"),
		tboday:document.querySelector("#tbody-1"),
		tboday2:document.querySelector("#tbody-2")

	},
	showBar(){
		const navLinks = document.querySelectorAll('.nav-link');
		const sections = document.querySelectorAll('.section');

		navLinks.forEach(link => {
			link.addEventListener('click', (e) => {
				e.preventDefault();
				
				navLinks.forEach(nav => nav.classList.remove('active'));
				sections.forEach(section => section.classList.remove('active'));

				link.classList.add('active');
				const targetSection = document.getElementById(link.dataset.section);
				targetSection.classList.add('active');
			});
		});
	},
	renderUser(user){
		this.element.name.textContent = user.data.name;
		const time = user.data.created_at.split("T")[0];
		this.element.time.textContent = `成為會員時間:${time}`;
	},
	renderAdvertiseCards(data) {
		const tboday = this.element.tboday;
		const tr = document.createElement("tr");
		const td0 = document.createElement("td");
		const img = document.createElement("img");

		img.src = data.images.split(",")[0];
		img.classList.add("img_box");

		td0.appendChild(img);
		tr.appendChild(td0);

		const td1 = document.createElement("td");
		td1.textContent = data.pet_name;
		tr.appendChild(td1);

		const td2 = document.createElement("td");
		td2.textContent = data.user_name ? data.user_name:"正在尋找家";
		tr.appendChild(td2);

		const td3 = document.createElement("td");
		td3.textContent = data.filled ? "是" : "否";
		tr.appendChild(td3);

		tboday.appendChild(tr);
	},
	renderAdoptCards(data) {
		const tboday = this.element.tboday2;
		const tr = document.createElement("tr");
		const td0 = document.createElement("td");
		const img = document.createElement("img");

		img.src = data.images.split(",")[0];
		img.classList.add("img_box");

		td0.appendChild(img);
		tr.appendChild(td0);

		const td1 = document.createElement("td");
		td1.textContent = data.pet_name;
		tr.appendChild(td1);

		const td2 = document.createElement("td");
		td2.textContent = data.sender_name;
		tr.appendChild(td2);

		const td3 = document.createElement("td");
		td3.textContent = data.filled ? "是" : "否";
		tr.appendChild(td3);

		tboday.appendChild(tr);
	},

	
}

const memberControl = {
	async init(){
		this.checkToken();
		memberView.showBar();
		const user = await memberModel.getUser();
		const advertiseForAdoption = await memberModel.advertise_for_adoption();
		for (let i = 0; i < advertiseForAdoption.data.length; i++) {
			memberView.renderAdvertiseCards(advertiseForAdoption.data[i]);
		}

		const wantToAdopt = await memberModel.want_to_adopt();
		console.log(wantToAdopt)
		for (let i = 0; i < wantToAdopt.data.length; i++) {
			memberView.renderAdoptCards(wantToAdopt.data[i]);
		}

		

		
		
		memberView.renderUser(user);
		this.logout();	
	},
	logout(){
		const btn = document.querySelector("#memberButton");
		btn.addEventListener("click",(e)=>{
			e.preventDefault();
			alert("登出成功");
			localStorage.removeItem("token");
			window.location.href = "/"
			return;
		})
	},
	checkToken(){
		const token = localStorage.getItem("token");
		if(token === null || token === undefined){
			alert("請登入");
			window.location.href = "/"
			return;
		}
	}

}

memberControl.init()