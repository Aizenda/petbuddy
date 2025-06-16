// ===== 表單渲染模組 (form-renderer.js) =====

// 使用DOM操作渲染表單
async function renderFormFromBackendData(backendData) {
	const data = await backendData;
	const form = data.form;
	const questions = form.questions;

	if (!form || !questions || !Array.isArray(questions)) {
			console.error('Invalid backend data format');
			return;
	}
	
	// 獲取表單容器
	const formContainer = document.getElementById('formContainer');
	
	// 清空現有內容
	formContainer.innerHTML = '';
	
	// 創建表單包裝器
	const formWrapper = createElement('div', 'form-wrapper');
	
	// 創建表單標題區域
	const formHeader = createFormHeader(form);
	formWrapper.appendChild(formHeader);
	
	// 創建表單內容區域
	const formContent = createElement('div', 'form-content');
	
	// 創建進度條
	const progressContainer = createProgressBar(questions.length);
	formContent.appendChild(progressContainer);
	
	// 創建表單元素
	const formElement = createElement('form', null, 'dynamicForm');
	
	// 創建問題列表
	questions.forEach((question, index) => {
			const questionCard = createQuestionCard(question, index);
			formElement.appendChild(questionCard);
	});
	
	formContent.appendChild(formElement);
	
	// 創建操作按鈕
	const formActions = createFormActions();
	formContent.appendChild(formActions);
	
	formWrapper.appendChild(formContent);
	formContainer.appendChild(formWrapper);
	
	// 初始化表單功能
	initializeForm(questions);
}

// ===== DOM 創建工具函數 =====

// 創建元素的輔助函數
function createElement(tag, className = null, id = null) {
	const element = document.createElement(tag);
	if (className) element.className = className;
	if (id) element.id = id;
	return element;
}

// 創建表單標題區域
function createFormHeader(form) {
	const header = createElement('div', 'form-header');
	
	const title = createElement('h1', 'form-title');
	title.textContent = form.formTitle || '表單填寫';
	header.appendChild(title);
	
	const meta = createElement('div', 'form-meta');
	
	const formIdDiv = createElement('div');
	formIdDiv.textContent = `表單編號: ${form.formId || 'N/A'}`;
	meta.appendChild(formIdDiv);
	
	const createdAtDiv = createElement('div');
	const createdAt = form.createdAt ? new Date(form.createdAt).toLocaleString('zh-TW') : 'N/A';
	createdAtDiv.textContent = `建立時間: ${createdAt}`;
	meta.appendChild(createdAtDiv);
	
	header.appendChild(meta);
	
	return header;
}

// 創建進度條
function createProgressBar(totalQuestions) {
	const container = createElement('div', 'progress-container');
	
	const progressBar = createElement('div', 'progress-bar');
	const progressFill = createElement('div', 'progress-fill');
	progressFill.id = 'progressFill';
	progressBar.appendChild(progressFill);
	container.appendChild(progressBar);
	
	const progressText = createElement('div', 'progress-text');
	progressText.id = 'progressText';
	progressText.textContent = `已完成 0 / ${totalQuestions} 題 (0%)`;
	container.appendChild(progressText);
	
	return container;
}

// 創建操作按鈕
function createFormActions() {
	const actions = createElement('div', 'form-actions');
	
	const resetBtn = createElement('button', 'form-btn form-btn-secondary');
	resetBtn.type = 'button';
	resetBtn.textContent = '重置表單';
	resetBtn.onclick = resetForm;
	actions.appendChild(resetBtn);
	
	const submitBtn = createElement('button', 'form-btn form-btn-primary');
	submitBtn.type = 'button';

	const path = window.location.pathname;

	if(path === "/revise"){
		submitBtn.textContent = '修改表單';
	}else{
		submitBtn.textContent = '提交表單';
		
	}
	submitBtn.onclick = submitForm; 
	actions.appendChild(submitBtn);
	
	return actions;
}

// ===== 問題卡片創建 =====

// 創建問題卡片
function createQuestionCard(question, index) {
	const questionKey = question.question_key;
	const questionType = question.type;
	const isRequired = question.required;
	const options = question.options || [];
	
	const card = createElement('div', 'question-card');
	card.setAttribute('data-question-key', questionKey);
	
	// 問題標題區域
	const header = createElement('div', 'question-header');
	
	const numberDiv = createElement('div', 'question-number');
	numberDiv.textContent = question.questionOrder || (index + 1);
	header.appendChild(numberDiv);
	
	const typeBadge = createElement('div', 'question-type-badge');
	typeBadge.textContent = getTypeDisplayName(questionType);
	header.appendChild(typeBadge);
	
	card.appendChild(header);
	
	// 問題標題
	const title = createElement('h3', 'question-title');
	title.innerHTML = `${question.title}${isRequired ? '<span class="required-mark">*</span>' : ''}`;
	card.appendChild(title);
	
	// 問題內容
	if (questionType === 'choice' && options.length > 0) {
			const isMultiple = question.isMultiple || question.multiple || false;
			const optionsContainer = createChoiceOptions(questionKey, options, isMultiple);
			card.appendChild(optionsContainer);
	} else if (questionType === 'image') {
			const imageContainer = createImageQuestion(question, questionKey);
			card.appendChild(imageContainer);
	} else {
			const textInput = createTextInput(questionKey);
			card.appendChild(textInput);
	}
	
	// 錯誤訊息
	const errorDiv = createElement('div', 'error-message');
	errorDiv.id = `error-${questionKey}`;
	card.appendChild(errorDiv);
	
	return card;
}

// 創建選擇題選項
function createChoiceOptions(questionKey, options, isMultiple) {
	const container = createElement('div', 'options-container');
	
	// 根據題目定義決定是否為多選
	const question = window.questionsData?.find(q => q.question_key === questionKey);
	const actualIsMultiple = question?.isMultiple || isMultiple || false;
	const inputType = actualIsMultiple ? 'checkbox' : 'radio';
	
	options.forEach((option, index) => {
			const optionItem = createElement('div', 'option-item');
			
			const input = createElement('input', 'option-input');
			input.type = inputType;
			input.id = `${questionKey}_opt_${index}`;
			input.name = questionKey;
			input.value = option.text || option.value || option;
			
			const label = createElement('label', 'option-label');
			label.setAttribute('for', `${questionKey}_opt_${index}`);
			label.textContent = option.text || option.value || option;
			
			optionItem.appendChild(input);
			optionItem.appendChild(label);
			container.appendChild(optionItem);
	});
	
	return container;
}

// 創建文字輸入
function createTextInput(questionKey) {
	const textarea = createElement('textarea', 'text-input');
	textarea.name = questionKey;
	textarea.placeholder = '請在此輸入您的答案...';
	return textarea;
}

// 創建圖片題
function createImageQuestion(question, questionKey) {
	const container = createElement('div', 'image-question-container');
	
	// 創建圖片顯示容器（如果有題目圖片）
	if (question.imageUrl || question.image_url || question.imagePath) {
			const questionImageContainer = createElement('div', 'question-image-container');
			const questionImg = createElement('img', 'question-image');
			questionImg.src = question.imageUrl || question.image_url || question.imagePath;
			questionImg.alt = question.title || '題目圖片';
			questionImg.loading = 'lazy';
			
			questionImg.onerror = function() {
					this.style.display = 'none';
					const placeholder = createElement('div', 'image-placeholder');
					placeholder.textContent = '題目圖片載入失敗';
					questionImageContainer.appendChild(placeholder);
			};
			
			questionImageContainer.appendChild(questionImg);
			container.appendChild(questionImageContainer);
	}
	
	// 創建上傳區域
	const uploadContainer = createElement('div', 'upload-container');
	
	// 創建隱藏的文件輸入
	const fileInput = createElement('input', 'file-input');
	fileInput.type = 'file';
	fileInput.id = `file_${questionKey}`;
	fileInput.name = questionKey;
	fileInput.accept = 'image/*';
	fileInput.style.display = 'none';
	
	// 創建上傳區域UI
	const uploadArea = createElement('div', 'upload-area');
	uploadArea.setAttribute('data-question-key', questionKey);
	
	const uploadIcon = createElement('div', 'upload-icon');
	uploadIcon.innerHTML = '📷';
	
	const uploadText = createElement('div', 'upload-text');
	uploadText.innerHTML = '<div class="upload-main-text">點擊或拖拽上傳圖片</div><div class="upload-sub-text">支援 JPG、PNG、JPEG 格式</div>';
	
	uploadArea.appendChild(uploadIcon);
	uploadArea.appendChild(uploadText);
	
	// 創建預覽區域
	const previewContainer = createElement('div', 'preview-container');
	previewContainer.style.display = 'none';
	
	const previewImage = createElement('img', 'preview-image');
	previewImage.id = `preview_${questionKey}`;
	
	const removeButton = createElement('button', 'remove-button');
	removeButton.type = 'button';
	removeButton.innerHTML = '✕';
	removeButton.title = '移除圖片';
	
	const imageInfo = createElement('div', 'image-info');
	imageInfo.id = `info_${questionKey}`;
	
	previewContainer.appendChild(previewImage);
	previewContainer.appendChild(removeButton);
	previewContainer.appendChild(imageInfo);
	
	uploadContainer.appendChild(fileInput);
	uploadContainer.appendChild(uploadArea);
	uploadContainer.appendChild(previewContainer);
	
	container.appendChild(uploadContainer);
	
	// 添加事件監聽器
	setupImageUploadEvents(questionKey, fileInput, uploadArea, previewContainer, previewImage, removeButton, imageInfo);
	
	return container;
}

// ===== 圖片處理 =====

// 設置圖片上傳事件
function setupImageUploadEvents(questionKey, fileInput, uploadArea, previewContainer, previewImage, removeButton, imageInfo) {
	// 點擊上傳區域觸發文件選擇
	uploadArea.addEventListener('click', () => {
			fileInput.click();
	});
	
	// 拖拽上傳功能
	uploadArea.addEventListener('dragover', (e) => {
			e.preventDefault();
			uploadArea.classList.add('dragover');
	});
	
	uploadArea.addEventListener('dragleave', (e) => {
			e.preventDefault();
			uploadArea.classList.remove('dragover');
	});
	
	uploadArea.addEventListener('drop', (e) => {
			e.preventDefault();
			uploadArea.classList.remove('dragover');
			
			const files = e.dataTransfer.files;
			if (files.length > 0) {
					handleImageFile(files[0], questionKey, previewContainer, previewImage, uploadArea, imageInfo);
			}
	});
	
	// 文件選擇事件
	fileInput.addEventListener('change', (e) => {
			const file = e.target.files[0];
			if (file) {
					handleImageFile(file, questionKey, previewContainer, previewImage, uploadArea, imageInfo);
			}
	});
	
	// 移除圖片事件
	removeButton.addEventListener('click', () => {
			removeImage(questionKey, fileInput, previewContainer, uploadArea);
	});
}

// 處理圖片文件（優化版，使用 Object URL）
function handleImageFile(file, questionKey, previewContainer, previewImage, uploadArea, imageInfo) {
	// 驗證文件類型
	if (!file.type.startsWith('image/')) {
			alert('請選擇圖片文件！');
			return;
	}
	
	// 驗證文件大小 (限制5MB)
	const maxSize = 5 * 1024 * 1024;
	if (file.size > maxSize) {
			alert('圖片大小不能超過 5MB！');
			return;
	}
	
	// 使用 Object URL 進行預覽（高效）
	const objectUrl = URL.createObjectURL(file);
	
	// 設置預覽
	previewImage.src = objectUrl;
	previewImage.onload = () => {
			// 圖片載入完成後釋放 Object URL
			URL.revokeObjectURL(objectUrl);
	};
	
	previewContainer.style.display = 'block';
	uploadArea.style.display = 'none';
	
	// 顯示文件信息
	const fileSize = (file.size / 1024).toFixed(1);
	imageInfo.textContent = `${file.name} (${fileSize} KB)`;
	
	// 只存儲必要的文件信息，不存 base64
	window.formAnswers[questionKey] = {
			file: file,
			name: file.name,
			size: file.size,
			type: file.type
	};
	
	updateProgress();
	clearError(questionKey);
}

// 移除圖片
function removeImage(questionKey, fileInput, previewContainer, uploadArea) {
	const previewImage = previewContainer.querySelector('.preview-image');
	
	// 如果使用 Object URL，需要釋放
	if (previewImage && previewImage.src.startsWith('blob:')) {
			URL.revokeObjectURL(previewImage.src);
	}
	
	previewContainer.style.display = 'none';
	uploadArea.style.display = 'flex';
	fileInput.value = '';
	
	// 清除答案
	delete window.formAnswers[questionKey];
	updateProgress();
}

// ===== 表單交互邏輯 =====

// 初始化表單功能
function initializeForm(questions) {
	// 答案存儲對象
	window.formAnswers = {};
	window.totalQuestions = questions.length;
	window.questionsData = questions;
	
	// 為所有輸入元素添加事件監聽器
	addEventListeners();
	
	// 初始化進度條
	updateProgress();
}

// 添加事件監聽器
function addEventListeners() {
	// 為選擇題添加事件
	document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
			input.addEventListener('change', function() {
					const questionKey = this.name;
					const value = this.value;
					const isMultiple = this.type === 'checkbox';
					
					handleChoiceInput(questionKey, value, isMultiple, this);
			});
	});
	
	// 為文字題添加事件
	document.querySelectorAll('.text-input').forEach(textarea => {
			textarea.addEventListener('input', function() {
					const questionKey = this.name;
					handleTextInput(questionKey, this.value);
			});
	});
	
	// 為選項容器添加點擊事件
	document.querySelectorAll('.option-item').forEach(item => {
			item.addEventListener('click', function(e) {
					if (e.target.type !== 'radio' && e.target.type !== 'checkbox') {
							const input = this.querySelector('input');
							if (input) {
									input.click();
							}
					}
			});
	});
}

// 處理選擇題輸入
function handleChoiceInput(questionKey, value, isMultiple, element) {
	// 獲取問題定義，確認是否為多選
	const question = window.questionsData.find(q => q.question_key === questionKey);
	const actualIsMultiple = question?.isMultiple || question?.multiple || isMultiple;
	
	if (actualIsMultiple) {
			// 多選題邏輯
			if (!window.formAnswers[questionKey]) {
					window.formAnswers[questionKey] = [];
			}
			
			if (element.checked) {
					if (!window.formAnswers[questionKey].includes(value)) {
							window.formAnswers[questionKey].push(value);
					}
			} else {
					window.formAnswers[questionKey] = window.formAnswers[questionKey].filter(item => item !== value);
			}
	} else {
			// 單選題邏輯
			if (element.checked) {
					window.formAnswers[questionKey] = value;
			} else {
					delete window.formAnswers[questionKey];
			}
	}
	
	updateProgress();
	clearError(questionKey);
	updateOptionStyles(questionKey);
}

// 處理文字輸入
function handleTextInput(questionKey, value) {
	window.formAnswers[questionKey] = value.trim();
	updateProgress();
	clearError(questionKey);
}

// ===== UI 更新功能 =====

// 更新進度條
function updateProgress() {
	const answeredCount = Object.keys(window.formAnswers).filter(key => {
			const answer = window.formAnswers[key];
			
			// 檢查對應題目類型
			const question = window.questionsData.find(q => q.question_key === key);
			if (question && question.type === 'image') {
					// 圖片題：檢查是否有上傳文件
					return answer && answer.file;
			} else if (Array.isArray(answer)) {
					return answer.length > 0;
			}
			return answer && answer.toString().trim().length > 0;
	}).length;
	
	const percentage = Math.round((answeredCount / window.totalQuestions) * 100);
	
	const progressFill = document.getElementById('progressFill');
	const progressText = document.getElementById('progressText');
	
	if (progressFill) progressFill.style.width = percentage + '%';
	if (progressText) progressText.textContent = `已完成 ${answeredCount} / ${window.totalQuestions} 題 (${percentage}%)`;
}

// 更新選項樣式
function updateOptionStyles(questionKey) {
	const questionCard = document.querySelector(`[data-question-key="${questionKey}"]`);
	if (!questionCard) return;
	
	const options = questionCard.querySelectorAll('.option-item');
	options.forEach(option => {
			const input = option.querySelector('input');
			if (input && input.checked) {
					option.classList.add('selected');
			} else {
					option.classList.remove('selected');
			}
	});
}

// ===== 錯誤處理 =====

// 清除錯誤訊息
function clearError(questionKey) {
	const errorElement = document.getElementById(`error-${questionKey}`);
	if (errorElement) {
			errorElement.style.display = 'none';
	}
}

// 顯示錯誤訊息
function showError(questionKey, message) {
	const errorElement = document.getElementById(`error-${questionKey}`);
	if (errorElement) {
			errorElement.textContent = message;
			errorElement.style.display = 'block';
	}
}

// ===== 表單驗證 =====

// 表單驗證
function validateForm() {
	let isValid = true;
	
	window.questionsData.forEach(question => {
			if (question.required) {
					const answer = window.formAnswers[question.question_key];
					let hasAnswer = false;
					
					if (question.type === 'image') {
							// 圖片題驗證：檢查是否有上傳文件
							hasAnswer = answer && answer.file;
					} else if (Array.isArray(answer)) {
							hasAnswer = answer.length > 0;
					} else {
							hasAnswer = answer && answer.toString().trim().length > 0;
					}
					
					if (!hasAnswer) {
							const errorMessage = question.type === 'image' ? '此題為必填項目，請上傳圖片' : '此題為必填項目，請填寫答案';
							showError(question.question_key, errorMessage);
							isValid = false;
					}
			}
	});
	
	return isValid;
}

// ===== 表單重置 =====

// 重置表單
function resetForm() {
	if (confirm('確定要重置表單嗎？所有填寫的內容將會清除。')) {
			const form = document.getElementById('dynamicForm');
			if (form) form.reset();
			
			window.formAnswers = {};
			updateProgress();
			
			// 清除所有錯誤訊息和選項樣式
			document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');
			document.querySelectorAll('.option-item.selected').forEach(el => el.classList.remove('selected'));
			
			// 清除圖片預覽
			document.querySelectorAll('.preview-container').forEach(container => {
					container.style.display = 'none';
			});
			document.querySelectorAll('.upload-area').forEach(area => {
					area.style.display = 'flex';
			});
	}
}

// ===== 工具函數 =====

// 獲取題目類型顯示名稱
function getTypeDisplayName(type) {
	const typeMap = {
			'choice': '選擇題',
			'text': '文字題',
			'image': '圖片題',
			'multiple': '多選題',
			'single': '單選題'
	};
	return typeMap[type] || '問答題';
}

// 獲取表單數據（不提交）
function getFormData() {
	const result = {
			formInfo: {
					formId: window.questionsData[0]?.formId || null,
					totalQuestions: window.totalQuestions,
					questionsData: window.questionsData
			},
			answers: {},
			files: {}
	};
	
	// 處理每個問題
	window.questionsData.forEach(question => {
			const questionKey = question.question_key;
			const userAnswer = window.formAnswers[questionKey];
			
			if (question.type === 'choice' && question.options && question.options.length > 0) {
					// 選擇題：根據DOM中的selected class判斷
					const questionCard = document.querySelector(`[data-question-key="${questionKey}"]`);
					const allOptions = question.options.map((option, index) => {
							const optionText = option.text || option.value || option;
							
							const optionElement = questionCard ? questionCard.querySelector(`#${questionKey}_opt_${index}`) : null;
							const optionItem = optionElement ? optionElement.closest('.option-item') : null;
							const isSelected = optionItem ? optionItem.classList.contains('selected') : false;
							
							return {
									text: optionText,
									selected: isSelected
							};
					});
					
					const selectedOptions = allOptions.filter(opt => opt.selected);
					
					result.answers[questionKey] = {
							type: 'choice',
							options: allOptions,
							selectedCount: selectedOptions.length,
							selectedValues: selectedOptions.map(opt => opt.text)
					};
					
			} else if (question.type === 'image' && userAnswer && userAnswer.file) {
					// 圖片文件
					result.files[questionKey] = userAnswer.file;
					result.answers[questionKey] = {
							type: 'image',
							fileName: userAnswer.name,
							fileSize: userAnswer.size,
							fileType: userAnswer.type,
							hasFile: true
					};
					
			} else {
					// 文字答案
					result.answers[questionKey] = {
							type: 'text',
							value: userAnswer || '',
							hasAnswer: !!(userAnswer && userAnswer.toString().trim())
					};
			}
	});
	
	return result;
}

// ===== 資料獲取 =====

// 獲取後端資料
async function getData() {
	const token = localStorage.getItem("token");
	if (token === null || token ===undefined){
			alert("請登入");
			window.location.href = '/login';
			return;
	};
	const postId =localStorage.getItem("postId") ;
	const path = window.location.pathname;
	if(path === "/read"){
		try{
			const req = await fetch(`/api/form/${postId}`, {
					method: "GET",
					headers: {
					Authorization: `Bearer ${token}`,
					},
			});

			const data = await req.json();
			if(!data.ok){
					throw Error(data.message);
			};

			return data;

		}catch (error){
				alert(`錯誤:${error.message}`);
				window.location.href = "/"
		};
	};
	try{
			const req = await fetch(`/api/form/${postId}`, {
					method: "GET",
					headers: {
					Authorization: `Bearer ${token}`,
					},
			});
			const data = await req.json();
			console.log(data)
			if(!data.ok){
					throw Error(data.message);
			};
			return data;
	}catch (error){
			alert(`錯誤:${error.message}`);
			window.location.href = "/"
	}


}

// ===== 初始化 =====

// 獲取後端資料並渲染表單
const backendData = getData();
renderFormFromBackendData(backendData);
