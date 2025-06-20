const userModel = {
	token : localStorage.getItem("token"),
	async updateAvatar(avatarData){
		try{
			const formData = new FormData();
			formData.append("file", avatarData); 
			const req = await fetch("/api/member/updata_avatar",{
				method:"PUT",
				headers:{
					"Authorization": `Bearer ${this.token}`,
				},
				body: formData
			});

			const data = await req.json();
			if(!data.ok){
				throw new Error(data.message);
			};

			return data;
		}catch (error){
			alert(error.message);
			return;
		}
	},
	async updateuserData(userData){
		try{
			const req = await fetch("/api/member/update_user",{
				method:"PUT",
				headers: {
					"Authorization": `Bearer ${this.token}`,
					"Content-Type": "application/json"
				},
				body:JSON.stringify(userData)
			});

			const data = await req.json()

			if(!data.ok){
				throw new Error(data.message)
			}
			return data;
		}catch(error){
			alert(error.message);
			return;
		}
	},
	async updatePassword(password){
		try{
			const req = await fetch("/api/member/update_password",{
				method:"PUT",
				headers: {
					"Authorization": `Bearer ${this.token}`,
					"Content-Type": "application/json"
				},
				body:JSON.stringify(password)
			});

			const data = await req.json()

			if(!data.ok){
				throw new Error(data.message)
			}
			return data;
		}catch(error){
			alert(error.message);
			return;
		}
	},
	async getUserDate(){
		try{
			const req = await fetch("/api/member/get_user_date",{
				method:"GET",
				headers: {
					"Authorization": `Bearer ${this.token}`,
					"Content-Type": "application/json"
				},
			});

			const data = await req.json()

			if(!data.ok){
				throw new Error(data.message)
			}
			return data;
		}catch(error){
			alert(error.message);
			return;
		}
	},
	async getAvatar(){
		try{
			const req = await fetch("/api/member/get_user_avatar",{
				method:"GET",
				headers: {
					"Authorization": `Bearer ${this.token}`,
					"Content-Type": "application/json"
				},
			});

			const data = await req.json()

			if(!data.ok){
				throw new Error(data.message)
			}
		}catch(error){
			alert(error.message);
			return;
		}
	},
}

const userView = {
	selectedFile:null,
	originalAvatarUrl: null,
	element:{
		headerAvatar:document.getElementById("headerAvatar"),
		avatarPreview:document.getElementById("avatarPreview"),
		avatarInput:document.getElementById("avatarInput"),
		btnUpload:document.querySelector(".btn-upload"),
		avatarOverlay:document.querySelector(".avatar-overlay"),
		btnRemove:document.querySelector(".btn-remove"),
		name:document.getElementById("name2"),
		phone:document.getElementById("phone"),
		email:document.getElementById("email"),
		address:document.getElementById("address"),
		profession:document.getElementById("profession"),	
		live:document.getElementById("live"),
		text:document.getElementById("text"),
		update_user:document.getElementById("update_user"),
		update_passwore:document.getElementById("update_passwore"),
		old_password:document.getElementById("old_password"),
		newpassword:document.getElementById("newpassword"),
		check_new_password:document.getElementById("check_new_password")
	},
	render(userDate){
		this.element.headerAvatar.src = userDate.avatar_url;
		this.element.avatarPreview.src = userDate.avatar_url;
		this.element.name.value = userDate.name || "姓名";
		this.element.phone.value = userDate.phone || "0912-345-678"
		this.element.email.value = userDate.email || "email@example.com";
		this.element.address.value = userDate.address || "";
		this.element.profession.value = userDate.occupation || "軟體工程師";
		this.element.text.textContent = userDate.pet_experience || "";
	},
	preview(){

		userView.element.avatarOverlay.addEventListener("click",()=>{
			userView.element.avatarInput.click();
		});

		userView.element.avatarInput.addEventListener("change", (e) => {
			const file = e.target.files[0];
			if (file) {
				// 檢查檔案大小（5MB）
				if (file.size > 5 * 1024 * 1024) {
					alert("檔案大小不能超過 5MB");
					return;
				}

				this.selectedFile = file;
				// 檢查檔案是否為圖片
				if (!file.type.startsWith("image/")) {
					alert("請選擇圖片檔案");
					return;
				}
				const reader = new FileReader();
				reader.onload = function(event) {
					const imageUrl = event.target.result;
					userView.element.avatarPreview.src = imageUrl;
					userView.element.headerAvatar.src = imageUrl;
				};
				reader.readAsDataURL(file);
			}
		});

		userView.element.btnRemove.addEventListener("click", () => {
			this.removePreview();
		});
	},
	removePreview(){

		this.selectedFile = null;
		this.element.avatarInput.value = "";
		
		// 恢復到原始頭像
		if (this.originalAvatarUrl) {
			this.element.avatarPreview.src = this.originalAvatarUrl;
			this.element.headerAvatar.src = this.originalAvatarUrl;
		} else {
			// 如果沒有原始頭像，使用預設圖片
			const defaultAvatar = "/static/img/user.png"; // 替換為你的預設頭像路徑
			this.element.avatarPreview.src = defaultAvatar;
			this.element.headerAvatar.src = defaultAvatar;
		}
	}
}

const userControl = {
	async init(){
		const user = await userModel.getUserDate();
		userDate = user.data;
		
		userView.render(userDate);
		userView.preview();

		userView.element.btnUpload.addEventListener("click", async () => {
				// 檢查是否有選擇文件
				if (!userView.selectedFile) {
					alert("請先選擇要上傳的圖片");
					return;
				}

				try {
					// 禁用按鈕避免重複點擊
					userView.element.btnUpload.disabled = true;
					userView.element.btnUpload.textContent = "上傳中...";

					// 傳遞文件給 updateAvatar 方法
					const result = await userModel.updateAvatar(userView.selectedFile);
					
					if (result) {
						alert("頭像更新成功！");
						// 清除選中的文件
						userView.selectedFile = null;
						userView.element.avatarInput.value = "";
					}
				} catch (error) {
					console.error("上傳失敗:", error);
				} finally {
					// 恢復按鈕狀態
					userView.element.btnUpload.disabled = false;
					userView.element.btnUpload.textContent = "上傳照片";
				}
			});


		userView.element.update_user.addEventListener("click", async () => {
			try {
				// 禁用按鈕避免重複點擊
				userView.element.update_user.disabled = true;
				userView.element.update_user.textContent = "更新中...";

				// 收集所有用戶資料
				const userData = {
					name: userView.element.name.value.trim(),
					phone: userView.element.phone.value.trim(),
					email: userView.element.email.value.trim(),
					address: userView.element.address ? userView.element.address.value.trim() : "",
					profession: userView.element.profession.value.trim(),
					live: userView.element.live ? userView.element.live.value.trim() : "",
					pet_experience: userView.element.text.textContent.trim()
				};

				// 呼叫更新API
				const result = await userModel.updateuserData(userData);

				if (result) {
					alert("用戶資料更新成功！");
				}

			} catch (error) {
				console.error("更新失敗:", error);
				alert("更新失敗，請稍後再試");
			} finally {
				// 恢復按鈕狀態
				userView.element.update_user.disabled = false;
				userView.element.update_user.textContent = "更新資料";
			}
		});

		userView.element.update_passwore.addEventListener("click", async () => {
			try {
				// 禁用按鈕避免重複點擊
				userView.element.update_passwore.disabled = true;
				userView.element.update_passwore.textContent = "更新中...";

				// 安全地收集密碼資料
				const oldPassword = userView.element.old_password?.value?.trim() || "";
				const newPassword = userView.element.newpassword?.value?.trim() || "";
				const checkNewPassword = userView.element.check_new_password?.value?.trim() || "";

				// 基本驗證
				if (!oldPassword) {
					alert("請輸入目前密碼");
					return;
				}

				if (!newPassword) {
					alert("請輸入新密碼");
					return;
				}

				if (!checkNewPassword) {
					alert("請確認新密碼");
					return;
				}

				// 檢查新密碼是否一致
				if (newPassword !== checkNewPassword) {
					alert("新密碼與確認密碼不一致");
					return;
				}

				// 密碼強度驗證（可選）
				if (newPassword.length < 6) {
					alert("新密碼長度至少需要6個字元");
					return;
				}

				// 檢查新密碼是否與舊密碼相同
				if (oldPassword === newPassword) {
					alert("新密碼不能與目前密碼相同");
					return;
				}

				const passwordData = {
					old_password: oldPassword,
					new_password: newPassword
				};
				
				// 呼叫更新密碼API
				const result = await userModel.updatePassword(passwordData);

				if (result) {
					alert("密碼更新成功！");
					// 清空密碼欄位
					userView.element.old_password.value = "";
					userView.element.newpassword.value = "";
					userView.element.check_new_password.value = "";
				}

			} catch (error) {
				console.error("密碼更新失敗:", error);
				alert("密碼更新失敗，請稍後再試");
			} finally {
				// 恢復按鈕狀態
				userView.element.update_passwore.disabled = false;
				userView.element.update_passwore.textContent = "更新密碼";
			}
		});
	}
}


userControl.init()
