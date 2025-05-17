const loginModel = {

}

const loginView = {
    element:{
        signupContainer:document.querySelector(".signup-container"),
        signinContainer:document.querySelector(".signin-container"),
        verification:document.querySelector(".btn-verification"),
        signup:document.querySelector(".btn-signup"),
        signinBtn:document.querySelector("#signin-1"),
        signupBtn:document.querySelector("#signin-2")
    }   
}

const loginControl = {
    init(){
        loginView.element.signinBtn.addEventListener("click",() => {
            this.changeForm("signup")

        });

         loginView.element.signupBtn.addEventListener("click",() => {
            this.changeForm("signin");
        });
    },

     changeForm(from) {
        if (from === "signup") {
            if (loginView.element.signupContainer) {
                loginView.element.signupContainer.style.display = "none";
            }
            if (loginView.element.signinContainer) {
                loginView.element.signinContainer.style.display = "block";
            }
        } else if (from === "signin") {
            if (loginView.element.signinContainer) {
                loginView.element.signinContainer.style.display = "none";
            }
            if (loginView.element.signupContainer) {
                loginView.element.signupContainer.style.display = "block";
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", ()=>{
    loginControl.init()
})