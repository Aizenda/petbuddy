document.addEventListener("DOMContentLoaded", () => {
	const token = localStorage.getItem("token");
	if (!token) {
		alert("請登入");
		window.location.href = "/login";
		return;
	}

	const form = document.getElementById("sendForm");

	form.addEventListener("submit", async (e) => {
		e.preventDefault();

		const images = uploader.getImagesData();
		if (images.length === 0) {
			alert("請至少上傳一張圖片");
			return;
		}

		const formData = new FormData(form);

		// 加入圖片
		images.forEach(image => {
			formData.append("images", image.file);
		});

		try {
			const res = await fetch("/api/send", {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`
				},
				body: formData
			});

			const result = await res.json();
			console.log("後端回應：", result);

			if (res.ok && result.ok) {
				alert("送養資訊已成功刊登！");
				window.location.href = `/question/${result.post_id}`;
			} else {
				alert(result.error || "送出失敗，請稍後再試");
			}
		} catch (error) {
			console.error("送出發生錯誤：", error);
			alert("伺服器錯誤，請稍後再試");
		}
	});
});

class ImageUploader {
		constructor() {
				this.maxImages = 4;
				this.images = [];
				this.initElements();
				this.bindEvents();
		}

		initElements() {
				this.imageInput = document.getElementById('imageInput');
				this.imagesGrid = document.getElementById('imagesGrid');
				this.uploadArea = document.getElementById('uploadArea');
				this.statusBar = document.getElementById('statusBar');
				this.statusText = document.getElementById('statusText');
				this.remainingCount = document.getElementById('remainingCount');
				this.limitWarning = document.getElementById('limitWarning');
		}

		bindEvents() {
				this.imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
		}

		handleImageUpload(event) {
				const files = Array.from(event.target.files);
				
				files.forEach(file => {
						if (this.images.length < this.maxImages && file.type.startsWith('image/')) {
								this.addImage(file);
						}
				});
				
				// 清空input值
				event.target.value = '';
		}

		addImage(file) {
				const reader = new FileReader();
				reader.onload = (e) => {
						const imageData = {
								id: Date.now() + Math.random(),
								url: e.target.result,
								file: file
						};
						
						this.images.push(imageData);
						this.renderImages();
						this.updateStatus();
				};
				reader.readAsDataURL(file);
		}

		removeImage(imageId) {
				this.images = this.images.filter(img => img.id !== imageId);
				this.renderImages();
				this.updateStatus();
		}

		renderImages() {
				// 清除現有圖片
				const existingImages = this.imagesGrid.querySelectorAll('.image-item');
				existingImages.forEach(item => item.remove());

				// 渲染圖片
				this.images.forEach(image => {
						const imageElement = this.createImageElement(image);
						this.imagesGrid.insertBefore(imageElement, this.uploadArea);
				});

				// 更新上傳區域狀態
				if (this.images.length >= this.maxImages) {
						this.uploadArea.style.display = 'none';
				} else {
						this.uploadArea.style.display = 'flex';
				}
		}

		createImageElement(imageData) {
				const imageItem = document.createElement('div');
				imageItem.className = 'image-item';
				
				// 創建圖片元素
				const img = document.createElement('img');
				img.src = imageData.url;
				img.alt = '上傳的寵物照片';
				
				// 創建刪除按鈕
				const removeBtn = document.createElement('button');
				removeBtn.className = 'remove-btn';
				removeBtn.textContent = '×';
				removeBtn.addEventListener('click', () => {
						this.removeImage(imageData.id);
				});
				
				// 組裝元素
				imageItem.appendChild(img);
				imageItem.appendChild(removeBtn);
				
				return imageItem;
		}

		updateStatus() {
				const uploadedCount = this.images.length;
				const remaining = this.maxImages - uploadedCount;

				if (uploadedCount > 0) {
						this.statusBar.style.display = 'flex';
						this.statusText.textContent = `已上傳 ${uploadedCount} 張圖片`;
						this.remainingCount.textContent = `${remaining} 張剩餘`;
				} else {
						this.statusBar.style.display = 'none';
				}

				if (uploadedCount >= this.maxImages) {
						this.limitWarning.style.display = 'block';
				} else {
						this.limitWarning.style.display = 'none';
				}
		}

		// 獲取所有圖片數據（可用於表單提交）
		getImagesData() {
				return this.images;
		}

		// 獲取描述文字
		getDescription() {
				return document.getElementById('description').value;
		}
}


// 初始化上傳器
const uploader = new ImageUploader();

// 示例：獲取表單數據
function getFormData() {
	const form = document.getElementById("sendForm");
	const formData = new FormData(form);
	const data = {};

	formData.forEach((value, key) => {
		if (data[key]) {
			if (!Array.isArray(data[key])) {
				data[key] = [data[key]];
			}
			data[key].push(value);
		} else {
			data[key] = value;
		}
	});

	// 加上圖片檔案
	data.images = uploader.getImagesData().map(img => img.file);

	console.log("完整表單資料：", data);
	return data;
}