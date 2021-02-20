ZERO = 0
NEGATIVE_ONE_THIRD = -1/3
NEGATIVE_TWO_THIRD = -2/3
ONE = 1
TWO = 2

CS_ONE_MIN = 1
CS_ONE_MAX = 25
GA_ONE_MIN = 1
GA_ONE_MAX = 5


class Question(object):
    def __init__(self, question_table, answer_key):
        # Assuming question_table is a soup object (Tag).
        # answer_key is a dictionary mapping a question short ID to its key.
        # left_panel contains the answer options, right panel contains the
        # question's attributes (Question ID, Status, etc).
        left_panel, right_panel = question_table.select("table",
            _class="menu-tbl")

        right_panel_comps = [[cell.text for cell in row("td")]
                             for row in right_panel]
        self.qtype = right_panel_comps[0][1]
        self.long_id = right_panel_comps[1][1]
        self.status = right_panel_comps[2][1]
        self.chosen_options = []
        self.given_answer = None

        ques_tag = left_panel.select("img")[0]
        ques_bits = ques_tag.attrs['name'].split('.')[0].split('_')[-1]
        qid = ques_bits.split("q")[1]

        if ques_bits.lower().startswith("ga"):
            self.short_id = "g" + qid

            if GA_ONE_MIN <= int(qid) <= GA_ONE_MAX:
                self.qmarks = ONE
            else:
                self.qmarks = TWO
        else:
            self.short_id = "c" + qid

            if CS_ONE_MIN <= int(qid) <= CS_ONE_MAX:
                self.qmarks = ONE
            else:
                self.qmarks = TWO

        # XXX: Petty hack to bypass strange question numbering issue. Remove
        # when problem figured out.
        self.short_id = self.short_id.replace("c58", "c54")

        self._set_question_type(left_panel, right_panel)
        self._set_obtained_marks(left_panel, right_panel, answer_key)

        self.subject_id = answer_key[self.short_id][1]

    def _set_obtained_marks(self, left_panel, right_panel, answer_key):
        if self.qtype in ["MCQ", "MSQ"]:
            ans_key = answer_key[self.short_id][0].split(";")
            self.actual_ans = ans_key

            if not self.chosen_options:
                self.obtained_marks = ZERO

            elif set(self.chosen_options) == set(ans_key):
                self.obtained_marks = self.qmarks

            elif self.qtype == "MCQ":
                if self.qmarks == ONE:
                    self.obtained_marks = NEGATIVE_ONE_THIRD
                else:
                    self.obtained_marks = NEGATIVE_TWO_THIRD
            elif self.qtype == "MSQ":
                self.obtained_marks = ZERO

        else:
            ans_key = answer_key[self.short_id][0]
            self.actual_ans = ans_key

            if ":" in ans_key:
                # We have a range, so let's check it.
                min_ans, max_ans = ans_key.split(":")

                if float(min_ans) <= float(self.given_answer) <= float(max_ans):
                    self.obtained_marks = self.qmarks
                else:
                    self.obtained_marks = ZERO
            else:
                # Direct string based comparison
                if ans_key == self.given_answer:
                    self.obtained_marks = self.qmarks
                else:
                    self.obtained_marks = ZERO


    def _set_question_type(self, left_panel, right_panel):
        if self.qtype in ["MCQ", "MSQ"]:
            chosen_options = right_panel.text.split(':')[-1]

            if "--" not in chosen_options:
                options = [int(option) for option in chosen_options.split(",")]

                for option in options:
                    # The img tags array has one extra element, the question
                    # itself, so it's like it's 1-indexed for answers.
                    # Deals with jumbled options by extracting the image name
                    # attribute of the chosen options.
                    # self.chosen_options looks like ["A", "B"] for MSQs and
                    # ["C"] for MCQs.
                    ans_tag = left_panel.select("img")[option]
                    self.chosen_options.append(
                        ans_tag.attrs['name'].split('.')[0].split('_')[-1][-1]
                        .upper()
                    )
        elif self.qtype == "NAT":
            try:
                given_answer = left_panel.text.split(':')[1]
                float(given_answer)
            except:
                # No answer given, so don't do anything
                pass
            else:
                if given_answer.startswith("."):
                    # .55 => 0.55
                    self.given_answer = "0" + given_answer
                elif given_answer.startswith("-."):
                    # -.55 => -0.55
                    self.given_answer = "-0." + given_answer[2:]
                else:
                    self.given_answer = given_answer

    def serialize(self):
        """
        Return in JSON format the required attributes of this question, acc
        to given answer key and response sheet.
        """
        res = {
            "short_id": self.short_id,
            "long_id": self.long_id,
            "question_type": self.qtype,
            "question_mark": self.qmarks,
            "subject_id": self.subject_id,
            "obtained_mark": self.obtained_marks,
        }

        if self.qtype in ["MCQ", "MSQ"]:
            res['response_given'] = ";".join(sorted(self.chosen_options))
            res['actual_ans'] = ";".join(sorted(self.actual_ans))
        else:
            res['response_given'] = self.given_answer or "N/A"
            res['actual_ans'] = self.actual_ans

        return res
