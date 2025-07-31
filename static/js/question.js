const questionModel = {
	async saveForm(data){
		const token = localStorage.getItem("token");

		try{
			const currentUrl = window.location.href;
			const postId = currentUrl.split("/").pop();
			console.log(postId)
			const req = await fetch(`/api/posts/${postId}/forms`, {
				method:"POST",
				headers:{
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json"
				},
				body: JSON.stringify(data),
			});

			const questionData = await req.json();
			if(!questionData.ok){
				throw new Error(questionData.message);
			};

			alert(questionData.message)
			return questionData

		}catch (e){
			alert(e)
			return e
		}

	},

}	

const questionView = {
	element: {
			questionBody: document.querySelector(".content-area"),
			title:document.querySelector("#title")
	},
	
	questionCount: 0,
	
	init() {
			this.updateContentArea();
	},
	
	updateContentArea() {
			const hasContent = this.element.questionBody.children.length > 1;
			if (hasContent) {
					this.element.questionBody.classList.add('has-content');
					this.element.questionBody.querySelector('.empty-state').style.display = 'none';
			} else {
					this.element.questionBody.classList.remove('has-content');
					this.element.questionBody.querySelector('.empty-state').style.display = 'block';
			}
	},
	
	createCardHeader(type, cardId) {
			const header = document.createElement("div");
			header.classList.add("card-header");
			
			const typeLabel = document.createElement("span");
			typeLabel.classList.add("card-type");
			typeLabel.textContent = type;
			
			const deleteBtn = document.createElement("button");
			deleteBtn.classList.add("delete-btn");
			deleteBtn.textContent = "×";
			deleteBtn.title = "刪除此題目";
			deleteBtn.addEventListener("click", () => {
					this.deleteCard(cardId);
			});
			
			header.appendChild(typeLabel);
			header.appendChild(deleteBtn);
			
			return header;
	},
	
	deleteCard(cardId) {
			const card = document.getElementById(cardId);
			if (card) {
					card.style.animation = 'fadeOut 0.3s ease';
					setTimeout(() => {
							card.remove();
							this.updateContentArea();
					}, 300);
			}
	},
	
	renderText() {
			this.questionCount++;
			const cardId = `card-${this.questionCount}`;
			const body = this.element.questionBody;
			
			const textDiv = document.createElement("div");
			textDiv.classList.add("div-card");
			textDiv.id = cardId;
			
			const header = this.createCardHeader("📝 文字題", cardId);
			
			const questionTitle = document.createElement("input");
			questionTitle.classList.add("title_style");
			questionTitle.placeholder = "請輸入題目標題...";
			questionTitle.required = true;
			
			const ans = document.createElement("textarea");
			ans.classList.add("ans_style");
			ans.placeholder = "用戶將在此輸入答案...";
			ans.rows = 4;
			ans.style.resize = "vertical";
			
			textDiv.appendChild(header);
			textDiv.appendChild(questionTitle);
			textDiv.appendChild(ans);
			body.appendChild(textDiv);
			
			this.updateContentArea();
			questionTitle.focus();
	},
	
	renderChoice() {
			this.questionCount++;
			const cardId = `card-${this.questionCount}`;
			const body = this.element.questionBody;
			const card = document.createElement("div");
			card.classList.add("div-card");
			card.id = cardId;
			
			const header = this.createCardHeader("☑️ 選擇題", cardId);
			
			const questionTitle = document.createElement("input");
			questionTitle.classList.add("title_style");
			questionTitle.placeholder = "請輸入選擇題題目...";
			questionTitle.required = true;
			
			const optionContainer = document.createElement("div");
			optionContainer.classList.add("option-container");
			
			let optionCount = 0;
			
			const addOption = () => {
					optionCount++;
					const optionDiv = this._createChoiceOption(optionCount, cardId, optionContainer);
					optionContainer.appendChild(optionDiv);
			};
			
			// 初始添加兩個選項
			addOption();
			addOption();
			
			const addBtn = document.createElement("button");
			addBtn.textContent = "➕ 新增選項";
			addBtn.type = "button";
			addBtn.classList.add("add-option-btn");
			addBtn.addEventListener("click", addOption);
			
			card.appendChild(header);
			card.appendChild(questionTitle);
			card.appendChild(optionContainer);
			card.appendChild(addBtn);
			body.appendChild(card);
			
			this.updateContentArea();
			questionTitle.focus();
	},
	
	renderImage() {
			this.questionCount++;
			const cardId = `card-${this.questionCount}`;
			const body = this.element.questionBody;
			const card = document.createElement("div");
			card.classList.add("div-card");
			card.id = cardId;
			
			const header = this.createCardHeader("🖼️ 圖片題", cardId);
			
			const questionTitle = document.createElement("input");
			questionTitle.classList.add("title_style");
			questionTitle.placeholder = "請輸入圖片題目標題...";
			questionTitle.required = true;
			
			const fileInput = document.createElement("input");
			fileInput.type = "file";
			fileInput.accept = "image/*";
			fileInput.classList.add("img-input");
			
			const uploadLabel = document.createElement("label");
			uploadLabel.textContent = "📁 點擊選擇圖片或拖拽到此處";
			uploadLabel.style.display = "block";
			uploadLabel.style.textAlign = "center";
			uploadLabel.style.cursor = "pointer";
			uploadLabel.style.padding = "20px";
			uploadLabel.appendChild(fileInput);
			
			const preview = document.createElement("img");
			preview.classList.add("img-preview");
			preview.style.display = "none";
			
			fileInput.addEventListener("change", (e) => {
					const file = e.target.files[0];
					if (!file) return;
					
					if (file.size > 5 * 1024 * 1024) {
							alert("圖片大小不能超過 5MB");
							return;
					}
					
					const reader = new FileReader();
					reader.onload = () => {
							preview.src = reader.result;
							preview.style.display = "block";
							uploadLabel.style.display = "none";
					};
					reader.readAsDataURL(file);
			});
			
			// 拖拽功能
			uploadLabel.addEventListener('dragover', (e) => {
					e.preventDefault();
					uploadLabel.style.background = '#e3f2fd';
			});
			
			uploadLabel.addEventListener('dragleave', () => {
					uploadLabel.style.background = '#f8f9ff';
			});
			
			uploadLabel.addEventListener('drop', (e) => {
					e.preventDefault();
					uploadLabel.style.background = '#f8f9ff';
					const files = e.dataTransfer.files;
					if (files.length > 0) {
							fileInput.files = files;
							fileInput.dispatchEvent(new Event('change'));
					}
			});
			
			card.appendChild(header);
			card.appendChild(questionTitle);
			card.appendChild(uploadLabel);
			card.appendChild(preview);
			body.appendChild(card);
			
			this.updateContentArea();
			questionTitle.focus();
	},
	
	_createChoiceOption(index, cardId, container) {
			const wrapper = document.createElement("div");
			wrapper.classList.add("choice-option");
			
			const label = document.createElement("label");
			label.textContent = `選項 ${index}`;
			label.style.fontWeight = "600";
			
			const radio = document.createElement("input");
			radio.type = "radio";
			radio.name = `choice_${cardId}`;
			radio.id = `choice_${cardId}_${index}`;
			
			const input = document.createElement("input");
			input.type = "text";
			input.placeholder = `請輸入選項 ${index} 內容...`;
			input.classList.add("ans_style");
			input.required = true;
			
			const removeBtn = document.createElement("button");
			removeBtn.classList.add("remove-option-btn");
			removeBtn.textContent = "×";
			removeBtn.title = "刪除此選項";
			removeBtn.type = "button";
			removeBtn.addEventListener("click", () => {
					if (container.children.length > 2) {
							wrapper.remove();
							this._updateOptionNumbers(container, cardId);
					} else {
							alert("至少需要保留兩個選項");
					}
			});
			
			wrapper.appendChild(label);
			wrapper.appendChild(radio);
			wrapper.appendChild(input);
			wrapper.appendChild(removeBtn);
			
			return wrapper;
	},
	
	_updateOptionNumbers(container, cardId) {
			const options = container.querySelectorAll('.choice-option');
			options.forEach((option, index) => {
					const label = option.querySelector('label');
					const radio = option.querySelector('input[type="radio"]');
					const input = option.querySelector('input[type="text"]');
					
					const newIndex = index + 1;
					label.textContent = `選項 ${newIndex}`;
					radio.id = `choice_${cardId}_${newIndex}`;
					input.placeholder = `請輸入選項 ${newIndex} 內容...`;
			});
	},
	
	clearAll() {
			if (confirm("確定要清空所有題目嗎？此操作無法復原。")) {
					const cards = this.element.questionBody.querySelectorAll('.div-card');
					cards.forEach(card => card.remove());
					this.questionCount = 0;
					this.updateContentArea();
			}
	},
	
	showPreview() {
			const cards = this.element.questionBody.querySelectorAll('.div-card');
			if (cards.length === 0) {
					alert("請先添加一些題目再預覽");
					return;
			}
			
			// 創建預覽窗口的文檔結構
			const previewWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
			const doc = previewWindow.document;
			
			// 設置基本文檔結構
			doc.open();
			doc.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>表單預覽</title></head><body></body></html>');
			doc.close();
			
			// 添加樣式
			const style = doc.createElement('style');
			
			// 創建樣式規則
			const styleRules = [
					'body { font-family: "Microsoft JhengHei", Arial, sans-serif; background: #f5f5f5; padding: 20px; margin: 0; }',
					'.preview-container { max-width: 600px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); }',
					'.preview-header { text-align: center; color: #333; margin-bottom: 30px; font-size: 2rem; }',
					'.question-item { margin-bottom: 25px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }',
					'.question-title { color: #333; margin-bottom: 15px; font-size: 1.2rem; font-weight: 600; }',
					'.question-type { color: white; font-size: 0.9rem; margin-bottom: 10px; background: #FFB627; padding: 4px 12px; border-radius: 15px; display: inline-block; }',
					'.option-item { margin: 8px 0; display: flex; align-items: center; gap: 8px; }',
					'.answer-area { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background: white; font-family: inherit; }',
					'.image-placeholder { padding: 40px; border: 2px dashed #ddd; text-align: center; color: #999; border-radius: 8px; }',
					'.preview-image { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }',
					'.close-btn { background: #FFB627; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 1rem; margin-top: 20px; }',
					'.close-btn:hover { background: #FF9400; }',
					'.center { text-align: center; }'
			];
			
			// 逐個添加樣式規則
			styleRules.forEach(rule => {
					try {
							style.sheet.insertRule(rule, style.sheet.cssRules.length);
					} catch (e) {
							// 如果 insertRule 不支持，回退到 textContent
							style.textContent += rule + '\n';
					}
			});
			doc.head.appendChild(style);
			
			// 創建主容器
			const container = doc.createElement('div');
			container.className = 'preview-container';
			
			// 添加標題
			const header = doc.createElement('h2');
			header.className = 'preview-header';
			header.textContent = this.element.title.value;
			container.appendChild(header);
			
			// 遍歷所有卡片並創建預覽內容
			cards.forEach((card, index) => {
					const title = card.querySelector('.title_style').value || '未填寫題目';
					const type = card.querySelector('.card-type').textContent;
					
					const questionDiv = doc.createElement('div');
					questionDiv.className = 'question-item';
					
					const typeSpan = doc.createElement('span');
					typeSpan.className = 'question-type';
					typeSpan.textContent = type;
					questionDiv.appendChild(typeSpan);
					
					const titleH3 = doc.createElement('h3');
					titleH3.className = 'question-title';
					titleH3.textContent = `${index + 1}. ${title}`;
					questionDiv.appendChild(titleH3);
					
					if (type.includes('選擇題')) {
							const options = card.querySelectorAll('.choice-option input[type="text"]');
							options.forEach((opt, i) => {
									const optText = opt.value || `選項 ${i + 1}`;
									const optionDiv = doc.createElement('div');
									optionDiv.className = 'option-item';
									
									const radio = doc.createElement('input');
									radio.type = 'radio';
									radio.disabled = true;
									radio.name = `preview_${index}`;
									
									const label = doc.createElement('label');
									label.textContent = optText;
									
									optionDiv.appendChild(radio);
									optionDiv.appendChild(label);
									questionDiv.appendChild(optionDiv);
							});
					} else if (type.includes('文字題')) {
							const textarea = doc.createElement('textarea');
							textarea.className = 'answer-area';
							textarea.rows = 3;
							textarea.disabled = true;
							textarea.placeholder = '用戶答案區域';
							questionDiv.appendChild(textarea);
					} else if (type.includes('圖片題')) {
							const img = card.querySelector('.img-preview');
							if (img && img.src && img.style.display !== 'none') {
									const previewImg = doc.createElement('img');
									previewImg.src = img.src;
									previewImg.className = 'preview-image';
									previewImg.alt = '預覽圖片';
									questionDiv.appendChild(previewImg);
							} else {
									const placeholder = doc.createElement('div');
									placeholder.className = 'image-placeholder';
									placeholder.textContent = '尚未上傳圖片';
									questionDiv.appendChild(placeholder);
							}
					}
					
					container.appendChild(questionDiv);
			});
			
			// 添加關閉按鈕
			const closeDiv = doc.createElement('div');
			closeDiv.className = 'center';
			const closeBtn = doc.createElement('button');
			closeBtn.className = 'close-btn';
			closeBtn.textContent = '關閉預覽';
			closeBtn.addEventListener('click', () => previewWindow.close());
			closeDiv.appendChild(closeBtn);
			container.appendChild(closeDiv);
			
			// 將容器添加到文檔
			doc.body.appendChild(container);
	},
	collectFormData() {
		const cards = this.element.questionBody.querySelectorAll('.div-card');
		const segments = window.location.pathname.split("/");
  	const postId = Number(segments.pop());
		const formData = {
				formTitle: this.element.title.value,
				postId:postId,
				questions: []
		};
		
		cards.forEach((card, index) => {
			const questionData = {
				id: index + 1,
				title: "",
				type: "",
				required: true,
				options: []
			};
			
			// 獲取題目標題
			const titleInput = card.querySelector('.title_style');
			if (titleInput) {
					questionData.title = titleInput.value.trim();
			}
			
			// 獲取題目類型
			const typeElement = card.querySelector('.card-type');
			if (typeElement) {
					const typeText = typeElement.textContent.trim();
					if (typeText.includes('文字題')) {
							questionData.type = 'text';
					} else if (typeText.includes('選擇題')) {
							questionData.type = 'choice';
					} else if (typeText.includes('圖片題')) {
							questionData.type = 'image';
					}
			}
				
			// 根據類型收集特定數據
			if (questionData.type === 'choice') {
					const optionInputs = card.querySelectorAll('.choice-option input[type="text"]');
					optionInputs.forEach((input, optIndex) => {
							const optionText = input.value.trim();
							if (optionText) {
									questionData.options.push({
											id: optIndex + 1,
											text: optionText,
											value: optionText
									});
							}
					});
			} else if (questionData.type === 'image') {
					const imagePreview = card.querySelector('.img-preview');
					if (imagePreview && imagePreview.src && imagePreview.style.display !== 'none') {
							questionData.imageUrl = imagePreview.src;
							questionData.hasImage = true;
					} else {
							questionData.hasImage = false;
					}
			}
			
			// 只添加有標題的題目
			if (questionData.title) {
					formData.questions.push(questionData);
			}
		});
		
		return formData;
	},
	validateFormData(formData) {
			const errors = [];

			if (!formData.formTitle || formData.formTitle.trim() === ""){
				errors.push("請填寫表單標題");
			}

			if (formData.questions.length === 0) {
				errors.push("請至少添加一個題目");
			};
			
			formData.questions.forEach((question, index) => {
					if (!question.title.trim()) {
							errors.push(`第 ${index + 1} 題缺少標題`);
					}
					
					if (question.type === 'choice' && question.options.length < 2) {
							errors.push(`第 ${index + 1} 題（選擇題）至少需要2個選項`);
					}
					
					if (question.type === 'choice') {
							const emptyOptions = question.options.filter(opt => !opt.text.trim());
							if (emptyOptions.length > 0) {
									errors.push(`第 ${index + 1} 題有空白選項，請填寫完整`);
							}
					}
			});
			
			return errors;
	},
	showLoading(buttonElement, originalText) {
			buttonElement.disabled = true;
			buttonElement.style.opacity = '0.6';
			buttonElement.textContent = '💾 儲存中...';
			return () => {
					buttonElement.disabled = false;
					buttonElement.style.opacity = '1';
					buttonElement.textContent = originalText;
			};
	},
	showSuccessMessage(title, message) {
			alert(`✅ ${title}\n${message}`);
			console.log(`成功: ${title} - ${message}`);
			
	},
	showErrorMessage(title, errors) {
			const errorText = Array.isArray(errors) ? errors.join('\n') : errors;
			alert(`❌ ${title}\n${errorText}`);
			console.error(`錯誤: ${title} - ${errorText}`);
	},
};

// 初始化
const questionControl = {
	
	init() {
		const token = localStorage.getItem("token")
		if(token === null || token === undefined){
			alert("請登入");
			window.location.href = "/login";
			return;
		};
		
		questionView.init();
		this.show()
	},
	show(){
		const save = document.querySelector("#save");

		save.addEventListener("click",async ()=>{
			const data = questionView.collectFormData();
			const validate = questionView.validateFormData(data);
			if(validate.length !== 0){
				alert(validate);
				return;
			};
			try{
				const req = await questionModel.saveForm(data);
				if(req.ok){
					window.location.href = "/member";
				}
			}catch(error){
				alert(error.message);
			}
			
		});
	}

};

questionControl.init();


// 添加樣式
const style = document.createElement('style');
style.textContent = `
		@keyframes fadeOut {
				from { opacity: 1; transform: translateY(0); }
				to { opacity: 0; transform: translateY(-20px); }
		}
`;
document.head.appendChild(style);