;;; workout-mode.el --- Simple Emacs mode for workout tracking -*- lexical-binding: t; -*-

;; Author: Your Name <your.email@example.com>
;; Version: 0.1
;; Package-Requires: ()
;; Keywords: convenience
;; URL: https://github.com/yourusername/workout-mode

;;; Commentary:
;; A simple Emacs minor mode for workout tracking integration.

;;; Code:

(defun workout-mode-greet ()
  "Print a greeting message in the minibuffer."
  (interactive)
  (message "Welcome to Workout Mode! Let's Fucking Go!"))

(defun workout-plan ()
  "Insert a Plan subheading and org table as a child of the heading at point, with cursor in the first cell."
  (interactive)
  (save-excursion
    (org-back-to-heading t)
    (org-end-of-meta-data t)
    (unless (bolp) (insert "\n"))
    (let* ((parent-level (org-current-level))
           (child-level (if parent-level (1+ parent-level) 2))
           (plan-heading (concat (make-string child-level ?*) " Plan\n|Exercise|Weight|Sets|Reps|\n|---|---|---|---|\n|       |      |    |    |\n")))
      (insert plan-heading)))
  (search-backward "|       |" nil t)
  (move-beginning-of-line nil)
  (org-table-align)
  (org-table-goto-column 1))

;;;###autoload
(define-minor-mode workout-mode
  "A minor mode for workout tracking integration."
  :lighter " Workout"
  :global t
  (if workout-mode
      (workout-mode-greet)))

(provide 'workout-mode)

;;; workout-mode.el ends here
