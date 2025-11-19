import random

from src.store.models import *
from src.payments.models import *
from src.payments.views import *





def send_test_transaction():
	# fake a transaction and send to customer
	user = User.objects.all().first()
	store = user.store_profile.user_store
	payment_method = user.payment_accounts.all().first()
	product_sold = store.products.all().first()
	codebase = product_sold.codebase

	amount_sold = 20

	codes_available = 5
	codes_to_send = get_x_codes(codes_available, codebase) 
	print(codes_to_send)

	what_is_left = amount_sold - codes_available 

	# if len()
	transaction = Transaction.objects.create(
		amount_paid=3.55,
		paid=True,
		store=store,
		payment_method=payment_method,
		buyer_email='williamusanga23@gmail.com',
	)
	order = transaction.items.create(
		product=product_sold,
		product_name=product_sold.name,
		quantity=amount_sold,
		price=product_sold.price,
	)
	
	context = {
	    'transaction': transaction,
	    'codes': codes_to_send,
	    'order': order,
	    'what_is_left': what_is_left,
	}
	Email.SendCustomerTransaction(context)




def get_x_codes(x, codebase):
	# this ensures to get x number of codes whether x is too much or too little compared to whats left
	codes = [code.id for code in codebase.codes.all()[:x]]
	whats_left = x-len(codes)

	for _ in range(whats_left):
		code = codebase.codes.create(code='test_'+str(random.random())[2:][:7])
		codes.append(code.id)

	return Code.objects.filter(id__in=codes)



if __name__ == '__main__':
	send_test_transaction()