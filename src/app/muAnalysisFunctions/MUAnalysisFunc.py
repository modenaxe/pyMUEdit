class MUAnalysisFunc:
    """Functionality handler for motor unit analysis operations.

    Provides methods for manipulating motor unit data including
    removal of specified MUs and data validation checks.
    """

    def __init__(self):
        """Initialize the MU analysis functionality handler."""
        self.MUedition = None

    def data_loaded(self):
        """Check if MU edition data is currently loaded.

        Returns:
            Boolean indicating whether MUedition data is available
        """
        return self.MUedition is not None

    def remove_mus_by_range(self, input_text):
        """Remove motor units specified by input text with array-MU format.

        Args:
            input_text: String specifying MUs to remove in format:
                       - Single MU: "array-mu" (e.g., "1-5" removes MU 5 from array 1)
                       - Range: "array-start-end" (e.g., "1-3-7" removes MUs 3-7 from array 1)
                       - Multiple: comma-separated (e.g., "1-5,2-3-6")

        Removes specified motor units from the Pulsetrain data and updates
        associated dictionaries (Dischargetimes, silval, silvalcon) accordingly.
        Indices are 1-based in input but converted to 0-based internally.
        """
        mus_to_remove = []
        parts = input_text.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            sub_parts = [p.strip() for p in part.split("-")]

            if len(sub_parts) == 2:  # Single MU: array-mu
                array_idx = int(sub_parts[0]) - 1
                mu_idx = int(sub_parts[1]) - 1
                if array_idx < 0 or mu_idx < 0:
                    raise ValueError("Indices must be positive.")
                mus_to_remove.append((array_idx, mu_idx))
            elif len(sub_parts) == 3:  # MU range: array-start-end
                array_idx = int(sub_parts[0]) - 1
                mu_start_idx = int(sub_parts[1]) - 1
                mu_end_idx = int(sub_parts[2]) - 1
                if array_idx < 0 or mu_start_idx < 0 or mu_end_idx < 0:
                    raise ValueError("Indices must be positive.")
                if mu_end_idx < mu_start_idx:
                    raise ValueError("End of range cannot be smaller than start.")
                for mu_idx in range(mu_start_idx, mu_end_idx + 1):
                    mus_to_remove.append((array_idx, mu_idx))
            else:
                raise ValueError(
                    "Each part must be in 'array-mu' or 'array-start-end' format."
                )

        mus_to_remove = sorted(list(set(mus_to_remove)))

        grouped_removals = {}
        for array_idx, mu_idx in mus_to_remove:
            if array_idx not in grouped_removals:
                grouped_removals[array_idx] = []
            grouped_removals[array_idx].append(mu_idx)

        for array_idx, mu_indices_to_remove in grouped_removals.items():
            if array_idx >= len(self.MUedition["edition"]["Pulsetrain"]):
                # Silently ignore invalid array indices for now, or add user feedback
                continue

            num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

            valid_mu_indices_to_remove = [
                i for i in mu_indices_to_remove if i < num_mus
            ]

            if not valid_mu_indices_to_remove:
                continue

            indices_to_keep = [
                i for i in range(num_mus) if i not in valid_mu_indices_to_remove
            ]

            if len(indices_to_keep) == num_mus:
                continue

            self.MUedition["edition"]["Pulsetrain"][array_idx] = self.MUedition[
                "edition"
            ]["Pulsetrain"][array_idx][indices_to_keep, :]

            dicts_to_update = ["Dischargetimes", "silval", "silvalcon"]
            for dict_name in dicts_to_update:
                if dict_name in self.MUedition["edition"]:
                    current_dict = self.MUedition["edition"][dict_name]

                    new_dict = {
                        k: v for k, v in current_dict.items() if k[0] != array_idx
                    }

                    for new_mu_idx, old_mu_idx in enumerate(indices_to_keep):
                        if (array_idx, old_mu_idx) in current_dict:
                            new_dict[(array_idx, new_mu_idx)] = current_dict[
                                (array_idx, old_mu_idx)
                            ]

                    self.MUedition["edition"][dict_name] = new_dict

        # This function should ideally trigger updates in the UI,
        # e.g., by emitting a signal that the main window connects to.
        print("MUs removed, UI should be updated.")
