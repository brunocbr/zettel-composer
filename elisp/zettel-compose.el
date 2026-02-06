;;; zettel-compose.el --- Wrapper for zettel-compose.py -*- lexical-binding: t -*-

(defgroup zettel-compose nil
  "Wrapper for zettel-compose.py script."
  :group 'tools)

(defcustom zettel-compose-script-path "/usr/local/bin/zettel-compose"
  "Path to the zettel-compose.py script or MacOS app.
You need to use the MacOS app for BLE support."
  :type 'string
  :group 'zettel-compose)

(defun zettel-compose--build-args (options)
  "Build the argument list for zettel-compose.py based on OPTIONS."
  (let (args)
    (when (plist-get options :index-file)
      ;; Ensure the index file path is wrapped in quotes
      (push (format "\"%s\"" (plist-get options :index-file)) args))

    ;; -O, --output=
    (when (plist-get options :output)
      ;; Ensure the output file path is wrapped in quotes
      (push (format "-O \"%s\"" (plist-get options :output)) args))
    ;; -M, --stream-to-marked
    (when (plist-get options :stream-to-marked)
      (push "--stream-to-marked" args))
    ;; --writers-gadget
    (when (plist-get options :writers-gadget)
      (push "--writers-gadget" args))
    ;; --gadget-mac
    (when (plist-get options :gadget-mac)
      (push "--gadget-mac" args))
    ;; -H, --heading-identifier=
    (when (plist-get options :heading-identifier)
      (push (concat "--heading-identifier=" (plist-get options :heading-identifier)) args))
    ;; -W, --watch
    (when (plist-get options :watch)
      (push "--watch" args))
    ;; -s, --sleep-time=
    (when (plist-get options :sleep-time)
      (push (concat "--sleep-time=" (number-to-string (plist-get options :sleep-time))) args))
    ;; -n, --no-paragraph-headings
    (when (plist-get options :no-paragraph-headings)
      (push "--no-paragraph-headings" args))
    ;; --no-separator
    (when (plist-get options :no-separator)
      (push "--no-separator" args))
    ;; -C, --no-commented-references
    (when (plist-get options :no-commented-references)
      (push "--no-commented-references" args))
    ;; -S, --suppress-index
    (when (plist-get options :suppress-index)
      (push "--suppress-index" args))
    ;; -I (only-link-from-index)
    (when (plist-get options :only-link-from-index)
      (push "-I" args))
    ;; -t (quote zettel count)
    (when (plist-get options :quote-z-count)
      (push (concat "-t " (number-to-string (plist-get options :quote-z-count))) args))
    ;; -G (parallel texts selection)
    (when (plist-get options :parallel-texts-selection)
      (push (concat "-G " (plist-get options :parallel-texts-selection)) args))
    ;; -v (verbose)
    (when (plist-get options :verbose)
      (push "-v" args))
    ;; -h (handout mode)
    (when (plist-get options :handout-mode)
      (let ((handout-with-sections (plist-get options :handout-with-sections)))
        (push (concat "-h" (if handout-with-sections "+" "")) args)))
    ;; -P (parallel-texts-processor)
    (when (plist-get options :parallel-texts-processor)
      (push "-P" args))
    ;; -L, --link-all
    (when (plist-get options :link-all)
      (push "--link-all" args))
    ;; --custom-url=
    (when (plist-get options :custom-url)
      (push (concat "--custom-url=" (plist-get options :custom-url)) args))
    ;; --section-symbol=
    (when (plist-get options :section-symbol)
      (push (concat "--section-symbol=" (plist-get options :section-symbol)) args))
    ;; --no-title
    (when (plist-get options :no-title)
      (push "--no-title" args))
    ;; --insert-bib-ref
    (when (plist-get options :insert-bib-ref)
      (push "--insert-bib-ref" args))
    ;; --no-front-matter
    (when (plist-get options :no-front-matter)
      (push "--no-front-matter" args))
    ;; -X (extract-mode)
    (when (plist-get options :extract-mode)
      (push "-X" args))
    ;; Return the arguments
    args))

;; (defun zettel-compose-run (options)
;;   "Run the zettel-compose.py script with OPTIONS."
;;   (interactive
;;    (let ((output (read-string "Output file: " nil nil))
;;          (stream-to-marked (yes-or-no-p "Stream to marked? "))
;;          (watch (yes-or-no-p "Watch the input file? ")))
;;      (list (list :output output
;;                  :stream-to-marked stream-to-marked
;;                  :watch watch
;;                  :index-file (buffer-file-name (current-buffer))))))
;;   (let* ((args (zettel-compose--build-args options))
;;          (command (mapconcat 'identity (cons zettel-compose-script-path args) " "))
;;          (output-buffer-name (generate-new-buffer-name "*zettel-compose-output*")))
;;     (message "Running command: %s" command)
;;     (start-process-shell-command "*zettel-compose*" output-buffer-name command)))

;;;###autoload
(defun zettel-compose-run (options)
  "Run the zettel-compose script.
If zettel-compose-script-path is a .app, use 'open -a'. Otherwise, run directly."
  (interactive
   (let ((output (read-string "Output file: " nil nil))
         (stream-to-marked (yes-or-no-p "Stream to marked? "))
         (watch (yes-or-no-p "Watch the input file? ")))
     (list (list :output output
                 :stream-to-marked stream-to-marked
                 :watch watch
                 :index-file (buffer-file-name (current-buffer))))))
  (let* ((args (zettel-compose--build-args options))
         (is-app (string-suffix-p ".app" zettel-compose-script-path))
         ;; Build the final command string
         (command (if is-app
                      (format "open %s --args %s"
                              (shell-quote-argument zettel-compose-script-path)
                              (mapconcat 'identity args " "))
                    (mapconcat 'shell-quote-argument
                               (cons zettel-compose-script-path args) " ")))
         (output-buffer-name (generate-new-buffer-name "*zettel-compose-output*")))

    (message "Running command: %s" command ", args: %s" args)
    (start-process-shell-command "zettel-compose-process" output-buffer-name command)))

;;;###autoload
(defun zettel-compose-stop-all-processes ()
  "Stop all running asynchronous zettel-compose processes."
  (interactive)
  (let ((processes (cl-remove-if-not
                    (lambda (proc)
                      (when proc
                        (string-match-p "*zettel-compose*" (buffer-name (process-buffer proc)))))
                    (mapcar #'get-buffer-process (buffer-list)))))
    (if processes
        (progn
          (dolist (proc processes)
            (delete-process proc))
          (message "Stopped all zettel-compose processes."))
      (message "No running zettel-compose processes found."))))

(provide 'zettel-compose)

;;; zettel-compose.el ends here
