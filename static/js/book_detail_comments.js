const csrf = document.querySelector('input[name=csrfmiddlewaretoken]').value;
let button = document.querySelector('.submit_button');
let product_review = document.querySelector('.product_review')
let write_a_comment = document.querySelector('.write_comment')
let textarea = document.querySelector('textarea')


let mark_to_bg = {
    1: '173, 41, 31, .5',
    2: '227, 102, 93, .5',
    3: '227, 188, 98, .5',
    4: '175, 214, 103, .5',
    5: '110, 219, 77, .5',
};


textarea.addEventListener('keydown', autosize);             
function autosize(){
  var el = this;
  setTimeout(function(){
    el.style.cssText = 'height:auto; padding:0';
    el.style.cssText = 'height:' + el.scrollHeight + 'px';
  },0);
}


function create_comment(result) {
    let username = result['comment_info']['profile_username'];
    let image_url = result['comment_info']['profile_image'];
    let text = result['comment_info']['text'];
    let date_of_creation = result['comment_info']['date_of_creation'];
    let book_mark = result['comment_info']['book_mark'];
    let div = document.createElement('div');
    div.classList.add('product_review_by_user_container');
    div.innerHTML = `<div class="product_review_by_user" style="background-color: rgba(${mark_to_bg[book_mark]})">
                            <div class="user_info">
                                <img class="user_image" src="${image_url}" alt="">
                                <div class="user_name">${username}</div>
                                <div class="user_mark">${book_mark}/5</div>
                            </div>
                            <div class="user_review">
                                <div class="user_review_text">${text}</div>
                                <div class="user_review_date">${date_of_creation}</div>
                            </div>
                        </div>`
    product_review.append(div);
    return div
}

function remove_old_errors() {
    let old_erros = document.querySelectorAll('.errors_wrapper');
    if (old_erros) {
        for (let block of old_erros) {
            block.remove()
        }
    }
}

function add_errors_to_page(result) {
    let errors_div = document.createElement('div');
    errors_div.className = 'errors_wrapper';
    for (let error of Object.values(result['errors'])) {
        let error_div = document.createElement('div');
        error_div.className = 'error';
        error_div.innerText = error;
        errors_div.append(error_div);
    }
    write_a_comment.after(errors_div)
}

function change_count_of_books(result) {
    let url = result['comment_info']['url']
    let see_more_button = document.querySelector('.see_more_button')
    if (see_more_button) {
        let number = +see_more_button.outerText.split(' ')[2];
        see_more_button.innerText = `There are ${number + 1} more comments..`
    } else {
        let see_more_wrapper = document.createElement('div');
        see_more_wrapper.className = 'see_more_wrapper';
        let link = document.createElement('a');
        link.className = 'see_more_button';
        link.href = url;
        link.innerText = 'There are 1 more commets..';
        see_more_wrapper.append(link);
        product_review.after(see_more_wrapper)
    }
}


function post_request_and_process_the_result(headers, body) {
    fetch('', {
        method: 'POST',
        body: body,
        headers: headers
    }).then(result => result.json())
        .then(result => {
            console.log(result);
            // remove previous errors
            remove_old_errors();
            // if form has errors
            if (result['status'] == 'form_invalid') {
                add_errors_to_page(result);
                // form hasn`t errors
            } else {
                // if there are already 5 errors
                if (document.querySelectorAll('.product_review_by_user_container').length >= 5) {
                    change_count_of_books(result);
                } else {
                    create_comment(result);
                }
            }
        })
}

button.addEventListener('click', e => {
    e.preventDefault();
    let form = document.forms.comment_form;
    let formDate = new FormData(form);
    headers = {
        "X-Requested-With": "XMLHttpRequest",
    };
    post_request_and_process_the_result(headers, formDate);
    form.reset()
})






























