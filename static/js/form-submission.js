// 驗證提交資料完整性（更新版，包含 ID 檢查和嚴格圖片格式限制）
function validateSubmissionData() {
    const errors = [];
    
    if (!window.formAnswers) {
        errors.push('表單答案物件不存在');
    }
    
    if (!window.questionsData) {
        errors.push('問題資料不存在');
    }
    
    if (!window.totalQuestions) {
        errors.push('問題總數未設定');
    }
    
    // 檢查必填題目
    if (window.questionsData) {
        window.questionsData.forEach(question => {
            if (question.required) {
                const answer = window.formAnswers[question.question_key];
                if (!answer) {
                    errors.push(`必填題目 "${question.title}" 未填寫`);
                }
            }
            
            // 檢查問題是否有 ID
            if (!question.id && !question.questionId) {
                errors.push(`問題 "${question.question_key}" 缺少 questionId`);
            }
        });
    }
    
    // 檢查圖片檔案（只允許 JPG/JPEG，最大 5MB）
    Object.entries(window.formAnswers || {}).forEach(([key, answer]) => {
        const question = window.questionsData?.find(q => q.question_key === key);
        if (question?.type === 'image' && answer.file) {
            // 檢查檔案大小
            if (answer.file.size > 5 * 1024 * 1024) {
                errors.push(`圖片 "${answer.name}" 超過 5MB 限制`);
            }
            
            // 嚴格檢查檔案格式（只允許 JPG/JPEG）
            const allowedTypes = ['image/jpeg', 'image/jpg'];
            const fileType = answer.file.type.toLowerCase();
            const fileName = answer.file.name.toLowerCase();
            const fileExtension = fileName.split('.').pop();
            
            if (!allowedTypes.includes(fileType) || !['jpg', 'jpeg','png'].includes(fileExtension)) {
                errors.push(`檔案 "${answer.name}" 必須是 JPG、JPEG、PNG 格式`);
            }
        }
    });
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

// 前端檔案上傳驗證函數（在檔案選擇時立即執行）
function validateImageFile(file, questionKey) {
    const errors = [];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    // 檢查檔案大小
    if (file.size > maxSize) {
        errors.push(`檔案大小超過 5MB 限制（目前: ${(file.size / 1024 / 1024).toFixed(2)}MB）`);
    }
    
    // 嚴格檢查檔案格式
    const allowedTypes = ['image/jpeg', 'image/jpg'];
    const fileType = file.type.toLowerCase();
    const fileName = file.name.toLowerCase();
    const fileExtension = fileName.split('.').pop();
    
    if (!allowedTypes.includes(fileType) || !['jpg', 'jpeg'].includes(fileExtension)) {
        errors.push('只支援 JPG 或 JPEG 格式的圖片');
    }
    
    // 額外檢查：確保檔案確實是圖片
    if (!file.type.startsWith('image/')) {
        errors.push('選擇的檔案不是有效的圖片格式');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// 檔案輸入處理函數（建議在檔案選擇事件中使用）
function handleImageFileSelect(event, questionKey) {
    const fileInput = event.target;
    const file = fileInput.files[0];
    
    if (!file) {
        // 清除之前的答案
        if (window.formAnswers && window.formAnswers[questionKey]) {
            delete window.formAnswers[questionKey];
        }
        return;
    }
    
    // 驗證檔案
    const validation = validateImageFile(file, questionKey);
    
    if (!validation.isValid) {
        // 顯示錯誤訊息
        alert('檔案驗證失敗：\n' + validation.errors.join('\n'));
        
        // 清除檔案選擇
        fileInput.value = '';
        
        // 清除表單答案
        if (window.formAnswers && window.formAnswers[questionKey]) {
            delete window.formAnswers[questionKey];
        }
        
        // 更新UI顯示
        updateImagePreview(questionKey, null);
        return;
    }
    
    // 檔案驗證通過，儲存到表單答案
    if (!window.formAnswers) {
        window.formAnswers = {};
    }
    
    window.formAnswers[questionKey] = {
        file: file,
        name: file.name,
        size: file.size,
        type: file.type
    };
    
    // 更新UI顯示
    updateImagePreview(questionKey, file);
}

// 更新圖片預覽UI（需要根據你的實際UI結構調整）
function updateImagePreview(questionKey, file) {
    const questionCard = document.querySelector(`[data-question-key="${questionKey}"]`);
    if (!questionCard) return;
    
    const previewContainer = questionCard.querySelector('.image-preview');
    const fileInfo = questionCard.querySelector('.file-info');
    
    if (file) {
        // 顯示檔案資訊
        if (fileInfo) {
            fileInfo.textContent = `已選擇: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`;
            fileInfo.style.color = '#28a745'; // 綠色表示成功
        }
        
        // 顯示圖片預覽
        if (previewContainer) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewContainer.innerHTML = `<img src="${e.target.result}" alt="預覽圖片" style="max-width: 200px; max-height: 200px; object-fit: cover;">`;
            };
            reader.readAsDataURL(file);
        }
    } else {
        // 清除顯示
        if (fileInfo) {
            fileInfo.textContent = '';
        }
        if (previewContainer) {
            previewContainer.innerHTML = '';
        }
    }
}

// 主要提交函數（保持原有邏輯，但增強驗證）
async function submitForm() {
    // 先進行完整驗證
    const dataValidation = validateSubmissionData();
    if (!dataValidation.isValid) {
        alert('提交驗證失敗：\n' + dataValidation.errors.join('\n'));
        return;
    }
    
    if (!validateForm()) {
        alert('請填寫所有必填項目！');
        return;
    }
    
    try {
        // 顯示載入狀態
        const submitBtn = document.querySelector('.form-btn-primary');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = '提交中...';
        submitBtn.disabled = true;
        
        const backendData = await getData();
        
        // 提取所需的 ID
        const formId = backendData.form.formId;
        const postId = backendData.form.postId || backendData.postId;
        const questionIds = extractQuestionIds(backendData.form.questions);
        
        // 統一使用 FormData 提交
        const path = window.location.pathname;
        if(path === "/revise"){
            const result = await submitFormUnified(formId, postId, questionIds);
            if(!result.ok){
                throw Error(result.message)
            }
            alert('表單更新成功！');
        }else{
            const result = await submitFormUnified(formId, postId, questionIds);
            if(!result.ok){
                throw Error(result.message)
            }
            alert('表單提交成功！');
        }

    } catch (error) {
        console.error('提交失敗:', error);
        alert(`提交失敗：${error.message}`);
    } finally {
        // 恢復按鈕狀態
        const submitBtn = document.querySelector('.form-btn-primary');
        if (submitBtn) {
            submitBtn.textContent = '提交表單';
            submitBtn.disabled = false;
        }
    }
}

// ===== 統一的 FormData 提交 =====

// 統一的 FormData 提交函數
async function submitFormUnified(formId, postId, questionIds) {
    const token = localStorage.getItem("token");
    const formData = new FormData();
    
    // 準備提交資料
    const submissionData = await prepareSubmissionData(formId, postId, questionIds);
    
    // 添加基本表單資料
    formData.append('formId', submissionData.formId || '');
    formData.append('postId', submissionData.postId || '');
    formData.append('formTitle', submissionData.formTitle || '');
    formData.append('submittedAt', submissionData.submittedAt);
    formData.append('totalQuestions', submissionData.totalQuestions.toString());
    
    // 處理每個問題的答案
    for (const [questionKey, answerData] of Object.entries(submissionData.answers)) {
        const originalAnswer = window.formAnswers[questionKey];
        const question = window.questionsData.find(q => q.question_key === questionKey);
        
        if (answerData.type === 'image' && originalAnswer && originalAnswer.file) {
            // 最後一次驗證圖片檔案
            const validation = validateImageFile(originalAnswer.file, questionKey);
            if (!validation.isValid) {
                throw new Error(`圖片檔案驗證失敗: ${validation.errors.join(', ')}`);
            }
            
            // 圖片題：分別添加檔案和 metadata
            formData.append(`image_${questionKey}`, originalAnswer.file);
            formData.append(`answer_${questionKey}`, JSON.stringify({
                type: 'image',
                questionId: question?.id || question?.questionId,
                fileName: answerData.fileName,
                fileSize: answerData.fileSize,
                fileType: answerData.fileType
            }));
        } else {
            // 其他題型：以 JSON 格式添加，包含 questionId
            const answerWithQuestionId = {
                ...answerData,
                questionId: question?.id || question?.questionId
            };
            formData.append(`answer_${questionKey}`, JSON.stringify(answerWithQuestionId));
        }
    }
    
    const path = window.location.pathname;
    if(path === "/revise"){
        const response = await fetch('/api/revise-form', {
            method: 'PUT',
            body: formData,
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.message)
        }
        return data

    }else{

        const response = await fetch('/api/submit-form', {
            method: 'POST',
            body: formData,
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.message)
        }

        return data
    }

}

// ===== ID 處理工具函數 =====

// 提取問題 ID 列表
function extractQuestionIds(questions) {
    if (!questions || !Array.isArray(questions)) {
        console.warn('問題資料格式不正確');
        return {};
    }
    
    const questionIds = {};
    questions.forEach(question => {
        const questionKey = question.question_key;
        const questionId = question.id || question.questionId;
        
        if (questionKey && questionId) {
            questionIds[questionKey] = questionId;
        }
    });
    
    console.log('提取的問題 ID 對應:', questionIds);
    return questionIds;
}

// 根據 questionKey 獲取對應的 questionId
function getQuestionId(questionKey, questionIds) {
    return questionIds[questionKey] || null;
}

// 驗證必要的 ID 是否存在
function validateRequiredIds(formId, postId, questionIds) {
    const errors = [];
    
    if (!formId) {
        errors.push('缺少 formId');
    }
    
    if (!postId) {
        errors.push('缺少 postId');
    }
    
    if (!questionIds || Object.keys(questionIds).length === 0) {
        errors.push('缺少 questionId 對應關係');
    }
    
    // 檢查每個已回答的問題是否都有對應的 questionId
    Object.keys(window.formAnswers || {}).forEach(questionKey => {
        if (!questionIds[questionKey]) {
            errors.push(`問題 "${questionKey}" 缺少對應的 questionId`);
        }
    });
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

// ===== 資料準備 =====

// 準備提交資料（支援 formId, postId, questionIds）
async function prepareSubmissionData(formId, postId, questionIds) {
    const formHeader = document.querySelector('.form-header');
    const formTitle = formHeader ? formHeader.querySelector('.form-title').textContent : '';
    
    // 驗證必要的 ID
    const validation = validateRequiredIds(formId, postId, questionIds);
    if (!validation.isValid) {
        console.error('ID 驗證失敗:', validation.errors);
        throw new Error(`資料不完整: ${validation.errors.join(', ')}`);
    }
    
    // 基本表單信息
    const baseData = {
        formId: formId || null,
        postId: postId || null,
        formTitle: formTitle,
        submittedAt: new Date().toISOString(),
        totalQuestions: window.totalQuestions,
        answers: {}
    };
    
    // 處理每個問題的答案
    window.questionsData.forEach(question => {
        const questionKey = question.question_key;
        const questionId = questionIds[questionKey];
        const userAnswer = window.formAnswers[questionKey];
        
        if (question.type === 'choice' && question.options && question.options.length > 0) {
            baseData.answers[questionKey] = processChoiceAnswer(question, questionKey, questionId);
            
        } else if (question.type === 'image' && userAnswer && userAnswer.file) {
            // 圖片答案：包含 questionId
            baseData.answers[questionKey] = {
                type: 'image',
                questionId: questionId,
                fileName: userAnswer.name,
                fileSize: userAnswer.size,
                fileType: userAnswer.type
            };
            
        } else {
            // 文字答案：包含 questionId
            baseData.answers[questionKey] = {
                type: 'text',
                questionId: questionId,
                value: userAnswer || ''
            };
        }
    });
    
    return baseData;
}

// 處理選擇題答案（加入 questionId）
function processChoiceAnswer(question, questionKey, questionId) {
    const isMultiple = question.isMultiple || question.multiple || false;
    
    // 根據DOM中的selected class來判斷選中狀態
    const questionCard = document.querySelector(`[data-question-key="${questionKey}"]`);
    const allOptions = question.options.map((option, index) => {
        const optionText = option.text || option.value || option;
        
        // 檢查對應的option-item是否有selected class
        const optionElement = questionCard ? questionCard.querySelector(`#${questionKey}_opt_${index}`) : null;
        const optionItem = optionElement ? optionElement.closest('.option-item') : null;
        const isSelected = optionItem ? optionItem.classList.contains('selected') : false;
        
        return {
            text: optionText,
            selected: isSelected,
            optionId: option.id || option.optionId || index // 支援選項ID
        };
    });
    
    // 獲取所有選中的選項
    const selectedOptions = allOptions.filter(opt => opt.selected);
    
    return {
        type: 'choice',
        questionId: questionId,
        questionType: question.type,
        isMultiple: isMultiple,
        options: allOptions,
        selectedValues: isMultiple ? 
            selectedOptions.map(opt => opt.text) : 
            (selectedOptions.length > 0 ? selectedOptions[0].text : null),
        selectedOptionIds: isMultiple ? 
            selectedOptions.map(opt => opt.optionId) : 
            (selectedOptions.length > 0 ? selectedOptions[0].optionId : null)
    };
}

// ===== 輔助函數 =====

// 檢查是否有圖片答案
function hasImageAnswers() {
    return Object.entries(window.formAnswers).some(([questionKey, answer]) => {
        const question = window.questionsData.find(q => q.question_key === questionKey);
        return question && question.type === 'image' && answer.file;
    });
}

