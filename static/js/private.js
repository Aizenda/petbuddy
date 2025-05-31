import { ModernPagination } from './next_page.js';

const privateModel = {
    async privateData(filters){
        try {
            const params = new URLSearchParams();

            for (const [key, value] of Object.entries(filters)) {
                if (value) params.append(key, value);
            }

            const res = await fetch(`/api/private?${params.toString()}`,{
                method:"GET"
            });
            const data = await res.json();

            if(!data.ok){
                throw new Error(data.error);
            }
            return data;

        } catch (error) {

            throw error;
        };


    } 
}

const privateView = {
    element:{
        card:document.querySelector(".public_card"),
        search:document.querySelector(".search-button")
    },
    createCardElement(){
        const cradElement = document.createElement("div");
        cradElement.classList.add("card_element");
        this.element.card.appendChild(cradElement);
    },

}

const privateControl = {
    async init(){
        const filters = {
            place: document.querySelector("#animal_place").value,
            kind: document.querySelector("#animal_kind").value,
            sex: document.querySelector("#animal_sex").value,
            color: document.querySelector("#animal_colour").value
        };
        const GetPrivateData = await privateModel.privateData(filters);
        for(let i=0; i < GetPrivateData.data.length; i++){
            privateView.createCardElement()
        }
    }
}

document.addEventListener("DOMContentLoaded", ()=>{
    privateControl.init()
})