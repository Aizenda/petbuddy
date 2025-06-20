// ===== 答案顯示模組 (form-answer-display.js) =====

// 使用DOM操作渲染表單答案（唯讀模式）
async function renderFormAnswersFromBackendData(backendData, answersData) {
	const data = await backendData;
    const ansPromies = await answersData;
	const answers = ansPromies.data;
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
	const formWrapper = createElement('div', 'form-wrapper answer-mode');
	
	// 創建表單標題區域
	const formHeader = createFormHeader(form, true); // true 表示答案模式
	formWrapper.appendChild(formHeader);
	
	// 創建表單內容區域
	const formContent = createElement('div', 'form-content');
	
	// 創建表單元素
	const formElement = createElement('form', 'answer-form', 'answerForm');
	
	// 創建問題列表（答案模式）
	questions.forEach((question, index) => {
		const questionCard = createAnswerQuestionCard(question, index, answers);
		formElement.appendChild(questionCard);
	});
	
	formContent.appendChild(formElement);
	formWrapper.appendChild(formContent);
	formContainer.appendChild(formWrapper);

}



// 創建答案問題卡片
function createAnswerQuestionCard(question, index, answers) {
	const questionKey = question.question_key;
	const questionType = question.type;
	const isRequired = question.required;
	const options = question.options || [];
	
	// 找到對應的答案 - 使用 questionId 作為 key
	const answer = answers[question.questionId];
	
	const card = createElement('div', 'question-card answer-card');
	card.setAttribute('data-question-key', questionKey);
	
	// 問題標題區域
	const header = createElement('div', 'question-header');
	
	const numberDiv = createElement('div', 'question-number');
	numberDiv.textContent = question.questionOrder || (index + 1);
	header.appendChild(numberDiv);
	
	const typeBadge = createElement('div', 'question-type-badge');
	typeBadge.textContent = getTypeDisplayName(questionType);
	header.appendChild(typeBadge);
	
	// 添加答案狀態標籤
	const statusBadge = createElement('div', 'answer-status-badge');
	const hasAnswer = checkIfAnswered(answer, questionType);
	statusBadge.textContent = hasAnswer ? '已答' : '未答';
	statusBadge.className = `answer-status-badge ${hasAnswer ? 'answered' : 'unanswered'}`;
	header.appendChild(statusBadge);
	
	card.appendChild(header);
	
	// 問題標題
	const title = createElement('h3', 'question-title');
	title.innerHTML = `${question.title}${isRequired ? '<span class="required-mark">*</span>' : ''}`;
	card.appendChild(title);
	
	// 問題內容和答案
	if (questionType === 'choice' && options.length > 0) {
		const answerContainer = createChoiceAnswerDisplay(questionKey, options, answer);
		card.appendChild(answerContainer);
	} else if (questionType === 'image') {
		const imageContainer = createImageAnswerDisplay(question, questionKey, answer);
		card.appendChild(imageContainer);
	} else {
		const textAnswer = createTextAnswerDisplay(questionKey, answer);
		card.appendChild(textAnswer);
	}
	
	return card;
}

// 創建選擇題答案顯示
function createChoiceAnswerDisplay(questionKey, options, answer) {
	const container = createElement('div', 'options-container');
	
	// 獲取選中的選項ID或值
	const selectedOptionId = answer ? answer.selected_option_id : null;
	const selectedValue = answer ? answer.selected_label : null;
	const selectedLabel = answer ? answer.selected_value : null;
	
	// 根據題目定義決定是否為多選（保持原本邏輯）
	const question = window.questionsData?.find(q => q.question_key === questionKey);
	const actualIsMultiple = question?.isMultiple || question?.multiple || false;
	const inputType = actualIsMultiple ? 'checkbox' : 'radio';
	
	options.forEach((option, index) => {

		const optionItem = createElement('div', 'option-item');
		const optionText = option.text || option.value || option;
		
		// 檢查是否為選中的選項 - 支援多種匹配方式
		let isSelected = false;
		if (selectedOptionId !== null && selectedOptionId !== undefined) {
			// 優先使用 option_id 匹配
			isSelected = option.optionId === selectedOptionId;

		} else if (selectedValue !== null && selectedValue !== undefined) {
			// 其次使用 value 匹配
			isSelected = (option.value === selectedValue);

		} else if (selectedLabel !== null && selectedLabel !== undefined) {
			// 最後使用 label 匹配
			isSelected = optionText === selectedLabel.toString();
    
		}
		// 如果是選中的選項，添加 selected class（保持原本樣式）
		if (isSelected) {
			optionItem.classList.add('selected');
		}
		
		// 創建 input 元素（但設為 disabled）
		const input = createElement('input', 'option-input');
		input.type = inputType;
		input.id = `${questionKey}_opt_${index}`;
		input.name = questionKey;
		input.value = optionText;
		input.checked = isSelected;
		input.disabled = true; 
		
		// 創建 label 元素
		const label = createElement('label', 'option-label');
		label.setAttribute('for', `${questionKey}_opt_${index}`);
		label.textContent = optionText;
		
		optionItem.appendChild(input);
		optionItem.appendChild(label);
		container.appendChild(optionItem);
	});
	
	// 如果沒有答案，顯示未作答提示
	if (!answer || (selectedOptionId === null && selectedValue === null && selectedLabel === null)) {
		const noAnswerDiv = createElement('div', 'no-answer-notice');
		noAnswerDiv.textContent = '此題未作答';
		container.appendChild(noAnswerDiv);
	}
	
	return container;
}

// 創建文字答案顯示
function createTextAnswerDisplay(questionKey, answer) {
	const container = createElement('div', 'answer-text-container');
	
	// 使用 answer.answer 而不是 answer.answer_text
	const answerText = answer ? answer.answer : null;
	
	if (answerText && answerText.toString().trim() !== '') {
		const textDisplay = createElement('div', 'answer-text-display');
		textDisplay.textContent = answerText;
		container.appendChild(textDisplay);
	} else {
		const noAnswerDiv = createElement('div', 'no-answer-notice');
		noAnswerDiv.textContent = '此題未作答';
		container.appendChild(noAnswerDiv);
	}
	
	return container;
}

// 創建圖片答案顯示
function createImageAnswerDisplay(question, questionKey, answer) {
	const container = createElement('div', 'answer-image-container');
	
	// 創建題目圖片顯示容器（如果有題目圖片）
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
	
	// 創建答案圖片顯示區域
	const answerImageContainer = createElement('div', 'answer-image-display');
	
	const imageUrl = answer ? answer.image_url : null;
	
	if (imageUrl) {
		const answerLabel = createElement('div', 'answer-label');
		answerLabel.textContent = '答案圖片：';
		answerImageContainer.appendChild(answerLabel);
		
		const answerImg = createElement('img', 'answer-image');
		answerImg.src = imageUrl;
		answerImg.alt = '答案圖片';
		answerImg.loading = 'lazy';
		
		answerImg.onerror = function() {
			this.style.display = 'none';
			const placeholder = createElement('div', 'image-placeholder');
			placeholder.textContent = '答案圖片載入失敗';
			answerImageContainer.appendChild(placeholder);
		};
		
		answerImageContainer.appendChild(answerImg);
	} else {
		const noAnswerDiv = createElement('div', 'no-answer-notice');
		noAnswerDiv.textContent = '此題未上傳圖片';
		answerImageContainer.appendChild(noAnswerDiv);
	}
	
	container.appendChild(answerImageContainer);
	return container;
}

// ===== 修改原有函數以支援答案模式 =====

// 修改創建表單標題區域函數
function createFormHeader(form, isAnswerMode = false) {
	const header = createElement('div', 'form-header');
	
	const title = createElement('h1', 'form-title');
	const titleText = isAnswerMode ? 
		`${form.formTitle || '表單填寫'} - 表單檢視` : 
		(form.formTitle || '表單填寫');
	title.textContent = titleText;
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

// ===== 工具函數 =====

function checkIfAnswered(answer, questionType) {
	if (!answer) return false;
	
	if (questionType === 'choice') {
		// 檢查多種可能的答案屬性，與 createChoiceAnswerDisplay 邏輯一致
		const selectedOptionId = answer.selected_option_id;
		const selectedValue = answer.selected_value;
		const selectedLabel = answer.selected_label;
		
		// 只要有任一屬性存在且不為空，就視為已作答
		return (selectedOptionId !== null && selectedOptionId !== undefined) ||
		       (selectedValue !== null && selectedValue !== undefined && selectedValue !== '') ||
		       (selectedLabel !== null && selectedLabel !== undefined && selectedLabel !== '');
		       
	} else if (questionType === 'image') {
		return answer.image_url !== null && answer.image_url !== undefined && answer.image_url !== '';
		
	} else if (questionType === 'text') {
		return answer.answer !== null && answer.answer !== undefined && answer.answer.toString().trim() !== '';
	}
	
	return false;
}


const postId = localStorage.getItem("postId");
const userId = localStorage.getItem("userId");
console.log(userId)
async function answersData(postId,userId){

    const token = localStorage.getItem("token");
    if (token === null && token === undefined){
        return;
    };
    
    try{
        const req = await fetch(`/api/ans?post_id=${postId}&user_id=${userId}`,{
            method:"GET",
            headers: {
            Authorization: `Bearer ${token}`,
            }
        });
        
        if (req.status === 403) {
            alert("你無權查看這張表單");
            window.location.href = "/member";
            return;
        }   
        const data = await req.json();

        if(!data.ok){
            throw new Error(data.message);
        }

        return data;
    } catch(error){
        alert(`錯誤:${error.message}`); 
        return;
    }
}



renderFormAnswersFromBackendData(backendData, answersData(postId,userId))