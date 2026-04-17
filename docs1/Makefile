.PHONY: create-practice remove-practice

create-practice:
ifndef NAME
	$(error NAME is not defined)
endif
	mkdir -p $(NAME)

remove-practice:
ifdef NAME
	$(error NAME is not defined)
endif
	rm -rf $(NAME)