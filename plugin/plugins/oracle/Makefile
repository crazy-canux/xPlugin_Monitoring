# Main targets
clean: clean-bytecode clean-backup
	@dh_clean

distclean: clean clean-build

# Sub targets
clean-build:
	@echo "Cleaning package creation directory..."
	@rm -rf $(CURDIR)/pkg-build

clean-bytecode:
	@echo 'Cleaning Python byte code files...'
	@find $(CURDIR) -name '*.pyc' -exec rm -f {} +
	@find $(CURDIR) -name '*.egg-info' -type d -exec rm -rf {} +
	@find $(CURDIR) -name '*.pyo' -exec rm -f {} +

clean-backup:
	@echo 'Cleaning backup files...'
	@find $(CURDIR) -name '*~' -exec rm -f {} +
	@find $(CURDIR) -name '#*#' -exec rm -f {} +
