const detailsMode = {
	async getDate(){
		const id = location.pathname.split("/").pop();
		const token = localStorage.getItem("token");
		try{
			const req = await fetch(`/api/details/${id}`,{
			method:"GET",
			headers: {
				"Authorization": `Bearer ${token}`,
				"Content-Type": "application/json"
			}
		});

		const data = await req.json();
		if(!data.ok){
			throw new Error(data.message);
		}
		return data;
		} catch (e){
			return e;
		};

	},
	async WantToAdopt(postId){
		const token = localStorage.getItem("token");
		try{
		const req = await fetch("/api/want_to_adopt", {
			method:"POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify({ "post_id": postId })
		});
		const data = await req.json();
		if(!data.ok){
			throw new Error(data.message);
		}
		console.log(data)
		return data;
		}catch (e){
			console.log(e);
			return e;
		}
	}
};

const detailsView = {
	element:{
		name:document.getElementById("pet_name"),
		img:document.querySelector(".image-container"),
		breed:document.getElementById("pet_breed"),
		sex:document.getElementById("pet_sex"),
		age:document.getElementById("pet_age"),
		bodyType:document.getElementById("pet_bodytype"),
		color:document.getElementById("pet_colour"),
		place:document.getElementById("pet_place"),
		ligationStatus:document.getElementById("pet_ligation_status"),
		date:document.getElementById("date"),
		describe:document.getElementById("pet_describe"),
		btn:document.querySelector(".btn-2")
	},
	render(data){
		this.element.name.textContent = data.pet_name;
		this.element.breed.textContent = data.pet_breed;
		this.element.sex.textContent = data.pet_sex;
		this.element.age.textContent = data.pet_age;
		this.element.bodyType.textContent = data.pet_bodytype;
		this.element.color.textContent = data.pet_colour;
		this.element.place.textContent = data.pet_place;
		this.element.ligationStatus.textContent = data.pet_ligation_status;
		this.element.date.textContent = data.created_at;
		this.element.describe.textContent = data.pet_describe;

	},
	renderImg(imgArray){
		for(let i=0;imgArray.length>i;i++){
			const imgs = document.createElement("img");
			imgs.classList.add("pet-image");
			imgs.src = imgArray[i];
			this.element.img.appendChild(imgs)
		}

		const container = document.querySelector(".image-container");
  	const images = container.querySelectorAll(".pet-image");
		const total = images.length;
		let currentIndex = 0;

		// 每秒切換一次
		const timer = setInterval(() => {
			currentIndex = (currentIndex + 1) % total;
			const width = container.clientWidth; 
			container.scrollTo({
				left: currentIndex * width,
				behavior: "smooth"
			});
		}, 3000);
	},
	cheackUSer(userId, postUserId){
		if (userId === postUserId){
			this.element.btn.style.display = "none";
		}
	}
}

const detailsControl = {
	async init(){
		let req = await detailsMode.getDate();
		this.cheackToken();

		const data = req.data;
		const img = data.images;
		const imgArray = JSON.parse(img); 
		const postUserId = data.user_id;
		const userId = req.user_id;
		const postId = data.id;

		detailsView.cheackUSer(userId , postUserId);
		detailsView.render(data);
		detailsView.renderImg(imgArray);


		detailsView.element.btn.addEventListener("click",async (e)=>{
			e.preventDefault();
			this.cheackToken();
			
			const WantToAdoptData = await detailsMode.WantToAdopt(postId);
			if(!WantToAdoptData.ok){
				alert(WantToAdoptData.message);
				return;
			}
			alert("已確認意願，靜候送養人通知")
		})
	},
	cheackToken(){
		const token = localStorage.getItem("token");
		if(token === null || token ==undefined){
			window.location.href = "/login";
			alert("未登入，請登入!!")
			return;
		};
	}
}

detailsControl.init();
