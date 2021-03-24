const csrf = document.querySelector('input[name=csrfmiddlewaretoken]').value;
let button = document.querySelector('.submit_button');
let product_review = document.querySelector('.product_review');


function create_elem(result) {
    let firstname = result['comment_info']['profile_first_name'];
    let image_url = result['comment_info']['profile_image'];
    let text = result['comment_info']['text'];
    let date_of_created = result['comment_info']['date_of_created'];
    let div = document.createElement('div');
    div.classList.add('product_review_by_user_container')
    div.innerHTML = `<div class="product_review_by_user">
                            <div class="user_info">
                                <img class="user_image" src="${image_url}" alt="">
                                <div class="user_name">${firstname}</div>
                            </div>
                            <div class="user_review">
                                <div class="user_review_text">${text}</div>
                                <div class="user_review_date">${date_of_created}</div>
                            </div>
                        </div>`
    product_review.append(div)
    return div
}

function post_request_and_create_elem(headers, body) {
    fetch('', {
        method: 'POST',
        body: body,
        headers: headers
    }).then(result => result.json())
        .then(result => {
            console.log(result)
            if (document.querySelectorAll('.product_review_by_user_container').length >= 5) {
                    let see_more_button = document.querySelector('.see_more_button')
                    let number = +see_more_button.outerText.split(' ')[2]
                    console.dir(see_more_button)
                    see_more_button.innerText = `There are ${number+1} more comments..`
            } else {
                create_elem(result)
            }
        })
}

button.addEventListener('click', e => {
    e.preventDefault();
    let form = document.forms[0]
    let formDate = new FormData(form);
    headers = {
        "X-Requested-With": "XMLHttpRequest",
    };
    post_request_and_create_elem(headers, formDate);
    form.reset()



})






























