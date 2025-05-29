const checkModel = {
	async check() {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch('/api/jwt', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await res.json();
      if (!data.ok) {
        throw new Error(data.message);
      }

      return data;
    } catch (error) {
      throw error;
    }
  } 
};

const checkView = {
  element: {
    loginButton: document.querySelector('#loginButton'),
    memberButton: document.querySelector('#memberButton')
  },

  changeMemberButton() {
    this.element.loginButton.style.display = 'none';
    this.element.memberButton.style.display = 'inline-block';
  },

	changeLoginButton(){
		this.element.loginButton.style.display = 'inline-block';
    this.element.memberButton.style.display = 'none';
	}
};

const checkControl = {
  async init() {
    try {
      await checkModel.check();
      checkView.changeMemberButton(); 
    } catch (error) {
      localStorage.removeItem('token')
      checkView.changeLoginButton();
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  checkControl.init();
});