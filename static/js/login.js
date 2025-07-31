const loginModel = {
  async send_code(phoneNumber) {
      const res =await  fetch('/api/auth/otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      const data = await res.json();

      if (!data.ok || !res.ok){
        throw new Error(data.message);
      };

      return data

  },

  async signup(userData) {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });

      const data = await res.json();
     
      if (!data.ok || !res.ok) {
        throw new Error(data.message);
      }
      
      return data;
  },

  async login(credentials) {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!data.ok) {
        throw new Error(data.message);
      }

      return data;
    } catch (error) {
      throw error;
    }
  },

};

const loginView = {
  element: {
    signupContainer: document.querySelector(".signup-container"),
    signinContainer: document.querySelector(".signin-container"),
    verification: document.querySelector(".btn-verification"),
    signup: document.querySelector(".btn-signup"),
    signinBtn: document.querySelector("#signin-1"),
    signupBtn: document.querySelector("#signin-2"),
    member: document.querySelector("#memberButton")
  },

  changeForm(from) {
    if (from === "signup") {
      if (this.element.signupContainer && this.element.signinContainer) {
        this.animateTransition(
          this.element.signupContainer,
          this.element.signinContainer
        );
      }
    } else if (from === "signin") {
      if (this.element.signinContainer && this.element.signupContainer) {
        this.animateTransition(
          this.element.signinContainer,
          this.element.signupContainer
        );
      }
    }
  },

  animateTransition(hideElement, showElement) {
    hideElement.style.position = "relative";
    showElement.style.position = "relative";

    hideElement.style.opacity = "1";
    hideElement.style.transform = "translateY(0)";
    hideElement.style.transition = "opacity 0.3s ease, transform 0.3s ease";

    setTimeout(() => {
      hideElement.style.opacity = "0";
      hideElement.style.transform = "translateY(-10px)";

      setTimeout(() => {
        hideElement.style.display = "none";
        showElement.style.display = "block";
        showElement.style.opacity = "0";
        showElement.style.transform = "translateY(10px)";
        showElement.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        showElement.offsetHeight;
        setTimeout(() => {
          showElement.style.opacity = "1";
          showElement.style.transform = "translateY(0)";
        }, 20);
      }, 300);
    }, 20);
  },

  showMessage(msg) {
    alert(msg);
  },

  validatePhoneNumber(phoneNumber) {
    const phoneRegex = /^09\d{8}$/;
    return phoneRegex.test(phoneNumber);
  },

  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
};

const loginControl = {
  init() {
    loginView.element.signinBtn.addEventListener("click", () => {
      loginView.changeForm("signup");
    });

    loginView.element.signupBtn.addEventListener("click", () => {
      loginView.changeForm("signin");
    });

  
    loginView.element.verification.addEventListener("click", async () => {
      const phoneInput = loginView.element.signupContainer.querySelector('input[name="phone"]');
      const phoneNumber = phoneInput.value.trim();

      if (!phoneNumber) {
        loginView.showMessage("請輸入電話號碼");
        return;
      }

      if (!loginView.validatePhoneNumber(phoneNumber)) {
        loginView.showMessage("請輸入有效的台灣手機號碼");
        return;
      }

      try {
        const result = await loginModel.send_code(phoneNumber);
        loginView.showMessage(result.message || "驗證碼已發送");
        this.startCountdown(loginView.element.verification);
      } catch (error) {
        loginView.showMessage("發送驗證碼失敗：" + error.message);
      }
    });

    // 註冊
    loginView.element.signup.addEventListener("click", async (e) => {
      e.preventDefault();

      const container = loginView.element.signupContainer;
      const otpInput = container.querySelector('input[name="num"]');
      const otpValue = otpInput.value.trim();

      if (!otpValue) {
        loginView.showMessage("請輸入驗證碼");
        return;
      }

      const userData = {
        name: container.querySelector('input[name="name"]')?.value.trim(),
        email: container.querySelector('input[name="email"]')?.value.trim(),
        password: container.querySelector('input[name="password"]')?.value,
        phone: container.querySelector('input[name="phone"]')?.value.trim(),
        otp: otpValue
      };

      if (!userData.name) {
        loginView.showMessage("請輸入姓名");
        return;
      }

      if (!userData.email || !loginView.validateEmail(userData.email)) {
        loginView.showMessage("請輸入有效的電子郵件");
        return;
      }

      if (!userData.password || userData.password.length < 6) {
        loginView.showMessage("密碼長度不足，至少需要6個字符");
        return;
      }

      if (!userData.phone || !loginView.validatePhoneNumber(userData.phone)) {
        loginView.showMessage("請輸入有效的台灣手機號碼");
        return;
      }

      try {
        const result = await loginModel.signup(userData);
        loginView.showMessage(result.message || "註冊成功");
        loginView.changeForm("signup");
      } catch (error) {
        loginView.showMessage("註冊失敗：" + error.message);
      }
    });

    // 登入
    const signinForm = loginView.element.signinContainer;
    const signinButton = signinForm.querySelector('.btn-signup');
    signinButton.addEventListener("click", async (e) => {
      e.preventDefault();

      const email = signinForm.querySelector('input[name="email"]')?.value.trim();
      const password = signinForm.querySelector('input[name="password"]')?.value;

      if (!email || !loginView.validateEmail(email)) {
        loginView.showMessage("請輸入有效的電子郵件");
        return;
      }

      if (!password || password.length < 6) {signup
        loginView.showMessage("請輸入正確密碼");
        return;
      }

      try {
        const result = await loginModel.login({ email, password });
        loginView.showMessage(result.message || "登入成功");
        localStorage.setItem("token", result.token);
        document.getElementById("loginButton").style.display = "none";
        document.getElementById("memberButton").style.display = "inline-block";
        window.location.href = "/"; 
      } catch (error) {
        loginView.showMessage("登入失敗：" + error.message);
      }
    });
  },

  startCountdown(button) {
    const seconds = 30;
    button.disabled = true;
    let countdown = seconds;
    const originalText = button.textContent || '發送驗證碼';

    button.textContent = `重新發送 (${countdown})`;

    const timer = setInterval(() => {
      countdown--;
      button.textContent = `重新發送 (${countdown})`;

      if (countdown <= 0) {
        clearInterval(timer);
        button.disabled = false;
        button.textContent = originalText;
      }
    }, 1000);
  }
};

document.addEventListener("DOMContentLoaded", async () => {
  loginControl.init();
});
