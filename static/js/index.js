const indexModel = {
	async getCount(){
		try{
			const req = await fetch("/api/count",{
				method: 'GET'
			});
			const data = await req.json();

			if(!data.ok){
				throw new Error(data.error);
			};

			return data
			
		} catch (error){
			console.error("getCount 錯誤：", error);
			throw error;
		}
	}
};

const indexView = {
	element:{
		dogCount:document.querySelector("#dog_count"),
		catCount:document.querySelector('#cat_count'),
		otherCount:document.querySelector('#other_count'),
		dogLink:document.querySelector('#dog_link'),
		catLink:document.querySelector('#cat_link'),
		otherLink:document.querySelector('#other_link'),
		all:document.querySelector('.view-all')
	},
	showCount(dog,cat,other){
		this.element.dogCount.textContent = dog
		this.element.catCount.textContent = cat
		this.element.otherCount.textContent = other
	}
}

const indexControl = {
	async init(){
		const data = await indexModel.getCount()
		indexView.showCount(data.dog, data.cat, data.other)
		indexView.element.dogLink.addEventListener('click', ()=>{
			window.location.href = '/publicAdoption?kind=狗'
		})
		indexView.element.catLink.addEventListener('click', ()=>{
			window.location.href = '/publicAdoption?kind=貓'
		})
		indexView.element.otherLink.addEventListener('click', ()=>{
			window.location.href = '/publicAdoption?kind=其他'
		})
		indexView.element.all.addEventListener('click', ()=>{
			window.location.href = '/publicAdoption?kind='
		})
	}
}

document.addEventListener('DOMContentLoaded',()=>{
	indexControl.init()
})