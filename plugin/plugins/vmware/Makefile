# Main targets
clean: clean-bytecode clean-backup clean-doc
	@dh_clean

distclean: clean
	@echo "Cleaning package creation directory..."
	@rm -rf ./pkg-build

# Sub targets
clean-doc:
	@echo "Removing generated documentation..."
	@rm -rf ./docs/build/*

clean-bytecode:
	@echo 'Cleaning Python byte code files...'
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +

clean-backup:
	@echo 'Cleaning backup files...'
	@find . -name '*~' -exec rm -f {} +
	@find . -name '#*#' -exec rm -f {} +

