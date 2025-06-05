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
	}
}

const memberView = {
	element:{
		name:document.getElementById("name"),
		time:document.getElementById("time")
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
		console.log(user)
		this.element.name.textContent = user.data.name;
		const time = user.data.created_at.split("T")[0];
		this.element.time.textContent = `成為會員時間:${time}`;
	}
}

const memberControl = {
	async init(){
		memberView.showBar();
		const user = await memberModel.getUser();
		memberView.renderUser(user);	
	},

}

memberControl.init()