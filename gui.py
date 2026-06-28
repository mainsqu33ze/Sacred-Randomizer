import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import traceback
import os

# Import core logic from your randomizer framework
# from randomizer import apply_config

class FE8RandomizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FE8 Sacred Stones Randomizer")
        self.geometry("750x650")
        self.minsize(650, 550)
        icon = tk.PhotoImage("D:\Fire_Emblem\Custom_randomizer\FE8-Custom-Randomizer\ai_cat_icon.png")
        self.iconphoto(True, icon)

        # Apply Modern Native Styling
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        
        # Color tweaks for modern accents
        self.style.configure(".", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("TNotebook", background="#e0e0e0", padding=2)
        self.style.configure("TNotebook.Tab", padding=[12, 4], font=("Segoe UI", 10, "bold"))
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)

        # --- GUI STATE VARIABLES ---
        # Paths & Global
        self.rom_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.seed = tk.StringVar(value="42")

        # Class Settings
        self.class_mode = tk.StringVar(value="shuffle")
        self.manakete_count = tk.IntVar(value=1)
        self.include_soldier = tk.BooleanVar(value=False)
        self.palette_mapping = tk.BooleanVar(value=True)
        self.affinity_randomization = tk.BooleanVar(value=False)

        # Growth Settings
        self.growth_char = tk.StringVar(value="false")
        self.growth_class = tk.StringVar(value="false")
        self.growth_buff_range = tk.DoubleVar(value=0.5)
        self.growth_min = tk.IntVar(value=0)
        self.growth_max = tk.IntVar(value=100)
        self.growth_stddev = tk.IntVar(value=10)

        # Base Stat Settings
        self.base_char = tk.StringVar(value="false")
        self.base_class = tk.StringVar(value="false")
        self.base_preserve = tk.BooleanVar(value=True)
        self.base_shuffle_con_mov = tk.BooleanVar(value=True)
        self.base_cross_tier = tk.BooleanVar(value=False)
        self.base_stddev = tk.IntVar(value=3)
        self.con_enabled = tk.BooleanVar(value=True)
        self.con_min = tk.IntVar(value=1)
        self.con_player_min = tk.IntVar(value=1)
        self.con_stddev = tk.IntVar(value=3)

        # Item & Loot Settings
        self.item_enabled = tk.BooleanVar(value=True)
        self.item_mode = tk.StringVar(value="random")
        self.item_rand_events = tk.BooleanVar(value=False)
        self.promo_enabled = tk.BooleanVar(value=True)
        self.promo_universal = tk.BooleanVar(value=True)
        self.promo_replace_dist = tk.BooleanVar(value=True)
        self.loot_enabled = tk.BooleanVar(value=False)
        self.loot_mode = tk.StringVar(value="random")

        # Weapon Settings
        self.wpn_enabled = tk.BooleanVar(value=False)
        self.wpn_might = tk.BooleanVar(value=True)
        self.wpn_hit = tk.BooleanVar(value=True)
        self.wpn_weight = tk.BooleanVar(value=True)
        self.wpn_crit = tk.BooleanVar(value=True)
        self.wpn_stddev = tk.IntVar(value=5)
        self.wpn_min_might = tk.IntVar(value=1)
        self.wpn_max_might = tk.IntVar(value=20)
        self.wpn_min_hit = tk.IntVar(value=30)
        self.wpn_max_hit = tk.IntVar(value=120)

        # Weapon Effects Weights
        self.fx_enabled = tk.BooleanVar(value=False)
        self.fx_poison = tk.IntVar(value=2)
        self.fx_nosferatu = tk.IntVar(value=3)
        self.fx_eclipse = tk.IntVar(value=1)
        self.fx_devil = tk.IntVar(value=5)
        self.fx_stone = tk.IntVar(value=1)

        # Enemy Settings
        self.enemy_enabled = tk.BooleanVar(value=True)
        self.enemy_classes = tk.BooleanVar(value=True)
        self.enemy_items = tk.BooleanVar(value=True)
        self.enemy_monsters = tk.BooleanVar(value=False)
        self.enemy_inc_monsters = tk.BooleanVar(value=False)
        self.enemy_inc_bosses = tk.BooleanVar(value=False)
        self.enemy_upgrade_chance = tk.IntVar(value=25)
        self.boss_growths_mode = tk.StringVar(value="false")
        self.boss_stats_mode = tk.StringVar(value="false")
        self.boss_max_ranks = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # --- Top Global Section ---
        top_frame = ttk.LabelFrame(self, text=" ROM Configuration ", padding=12)
        top_frame.pack(fill=tk.X, padx=12, pady=8)

        self._create_path_row(top_frame, "Input ROM File:", self.rom_path, self.browse_input, 0)
        self._create_path_row(top_frame, "Output ROM File:", self.output_path, self.browse_output, 1)

        ttk.Label(top_frame, text="Seed Profile (0 for Random):").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(top_frame, textvariable=self.seed, width=12).grid(row=2, column=1, sticky=tk.W, padx=6)

        # --- Tab Setup ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self._build_classes_tab()
        self._build_stats_tab()
        self._build_items_tab()
        self._build_weapons_tab()
        self._build_enemies_tab()

        # --- Bottom Action Bar ---
        bottom_frame = ttk.Frame(self, padding=12)
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="📁 Load config.yaml", command=self.load_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom_frame, text="💾 Save current config", command=self.save_config).pack(side=tk.LEFT, padx=4)
        
        btn_randomize = ttk.Button(bottom_frame, text="✨ Randomize ROM!", style="Action.TButton", command=self.run_randomizer)
        btn_randomize.pack(side=tk.RIGHT, padx=4)

    def _create_path_row(self, parent, label_text, var, command, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Entry(parent, textvariable=var, width=60).grid(row=row, column=1, sticky=tk.EW, padx=6, pady=4)
        ttk.Button(parent, text="Browse...", command=command).grid(row=row, column=2, padx=2)
        parent.columnconfigure(1, weight=1)

    def _create_scrollable_tab(self, name):
        """Creates a standardized scrollable tab architecture for scaling safely."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=name)
        
        canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0, background="#f5f5f5")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=10)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return scrollable_frame

    # --- Tab Builders ---
    def _build_classes_tab(self):
        tab = self._create_scrollable_tab("Classes")

        card = ttk.LabelFrame(tab, text=" Playable Class Shuffling ", padding=10)
        card.pack(fill=tk.X, pady=4)

        ttk.Label(card, text="Randomization Scheme:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Combobox(card, textvariable=self.class_mode, values=["false", "shuffle", "random"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(card, text="Guaranteed Manaketes:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(card, from_=0, to=5, textvariable=self.manakete_count, width=5).grid(row=1, column=1, padx=6, sticky=tk.W)

        ttk.Checkbutton(card, text="Allow Soldier Class Assignment (Player Units)", variable=self.include_soldier).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=4)
        ttk.Checkbutton(card, text="Preserve Customized Asset Palettes", variable=self.palette_mapping).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=4)

        card_misc = ttk.LabelFrame(tab, text=" Extra Features ", padding=10)
        card_misc.pack(fill=tk.X, pady=8)
        ttk.Checkbutton(card_misc, text="Randomize Unit Character Support Affinities", variable=self.affinity_randomization).pack(anchor=tk.W)

    def _build_stats_tab(self):
        tab = self._create_scrollable_tab("Stats & Growths")

        # Growths Frame
        g_card = ttk.LabelFrame(tab, text=" Stat Growth Profiles ", padding=10)
        g_card.pack(fill=tk.X, pady=4)

        ttk.Label(g_card, text="Player Unit Growths:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(g_card, textvariable=self.growth_char, values=["false", "shuffle", "random", "pool"], state="readonly").grid(row=0, column=1, padx=6, pady=2, sticky=tk.W)

        ttk.Label(g_card, text="Generic Enemy Growths:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(g_card, textvariable=self.growth_class, values=["false", "shuffle", "random", "random_buff", "pool"], state="readonly").grid(row=1, column=1, padx=6, pady=2, sticky=tk.W)

        ttk.Label(g_card, text="Gaussian Spread Standard Deviation:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(g_card, from_=1, to=50, textvariable=self.growth_stddev, width=6).grid(row=2, column=1, padx=6, pady=2, sticky=tk.W)

        # Base Stats Frame
        b_card = ttk.LabelFrame(tab, text=" Starting Base Stats ", padding=10)
        b_card.pack(fill=tk.X, pady=8)

        ttk.Label(b_card, text="Player Base Generation:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b_card, textvariable=self.base_char, values=["false", "shuffle", "random"], state="readonly").grid(row=0, column=1, padx=6, pady=2, sticky=tk.W)

        ttk.Label(b_card, text="Class Base Generation:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b_card, textvariable=self.base_class, values=["false", "shuffle", "random"], state="readonly").grid(row=1, column=1, padx=6, pady=2, sticky=tk.W)

        ttk.Checkbutton(b_card, text="Include Constitution & Movement in Shuffle arrays", variable=self.base_shuffle_con_mov).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Sub Frame for Con Controls - FIXED .grid() error here
        con_card = ttk.LabelFrame(b_card, text=" Dedicated Constitution (Con) Isolation ", padding=8)
        con_card.grid(row=3, column=0, columnspan=3, sticky="ew", pady=6, padx=2)
        
        ttk.Checkbutton(con_card, text="Enable Independent Con Control Rules", variable=self.con_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(con_card, text="Min Enemy Con:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(con_card, from_=1, to=20, textvariable=self.con_min, width=5).grid(row=1, column=1, padx=4, sticky=tk.W)

    def _build_items_tab(self):
        tab = self._create_scrollable_tab("Items & Progression")

        card_inv = ttk.LabelFrame(tab, text=" Unit Inventories ", padding=10)
        card_inv.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(card_inv, text="Enforce Inventory Adjustments to fit new Class weapon ranks", variable=self.item_enabled).pack(anchor=tk.W, pady=2)
        
        ttk.Label(card_inv, text="Inventory Engine:").pack(anchor=tk.W, pady=2)
        ttk.Combobox(card_inv, textvariable=self.item_mode, values=["random", "shuffle"], state="readonly").pack(anchor=tk.W, padx=15)

        card_promo = ttk.LabelFrame(tab, text=" Promotion Architecture ", padding=10)
        card_promo.pack(fill=tk.X, pady=8)
        ttk.Checkbutton(card_promo, text="Consolidate all Promotion Items into Universal Master Seals", variable=self.promo_enabled).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(card_promo, text="Replace item distribution logs with universal seals", variable=self.promo_replace_dist).pack(anchor=tk.W, pady=2)

        card_loot = ttk.LabelFrame(tab, text=" Strategic Objective Loot Tables ", padding=10)
        card_loot.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(card_loot, text="Randomize World Loot (Chests, Houses, Events)", variable=self.loot_enabled).pack(anchor=tk.W, pady=2)

    def _build_weapons_tab(self):
        tab = self._create_scrollable_tab("Weapons & Magic")

        w_card = ttk.LabelFrame(tab, text=" Baseline Scaling Parameters ", padding=10)
        w_card.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(w_card, text="Enable Algorithmic Weapon Variable Mutation", variable=self.wpn_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Checkbutton(w_card, text="Mutate Might (MT)", variable=self.wpn_might).grid(row=1, column=0, sticky=tk.W, padx=10)
        ttk.Checkbutton(w_card, text="Mutate Accuracy (HIT)", variable=self.wpn_hit).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(w_card, text="Mutate Weight (WT)", variable=self.wpn_weight).grid(row=2, column=0, sticky=tk.W, padx=10)
        ttk.Checkbutton(w_card, text="Mutate Critical Rate (CRT)", variable=self.wpn_crit).grid(row=2, column=1, sticky=tk.W)

        fx_card = ttk.LabelFrame(tab, text=" Random Weapon Effect Coefficients (Weights) ", padding=10)
        fx_card.pack(fill=tk.X, pady=8)
        ttk.Checkbutton(fx_card, text="Apply Secondary Status Infusion Engine", variable=self.fx_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=4)

        effects = [("Poison Chance Vector:", self.fx_poison), ("Nosferatu Siphon:", self.fx_nosferatu), 
                   ("Eclipse HP Decimation:", self.fx_eclipse), ("Devil Backfire Ratio:", self.fx_devil)]
        for idx, (label, var) in enumerate(effects):
            ttk.Label(fx_card, text=label).grid(row=idx+1, column=0, sticky=tk.W, pady=2)
            ttk.Spinbox(fx_card, from_=0, to=100, textvariable=var, width=5).grid(row=idx+1, column=1, padx=6, sticky=tk.W)

    def _build_enemies_tab(self):
        tab = self._create_scrollable_tab("Enemies & Combat")

        e_card = ttk.LabelFrame(tab, text=" Map Unit Generation ", padding=10)
        e_card.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(e_card, text="Enable Generic Enemy Class Re-allocation", variable=self.enemy_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        ttk.Label(e_card, text="Loadout Tier Upgrade Chance (%):").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(e_card, from_=0, to=100, textvariable=self.enemy_upgrade_chance, width=6).grid(row=1, column=1, sticky=tk.W, padx=4)

        ttk.Checkbutton(e_card, text="Include Boss Commanders inside distribution arrays", variable=self.enemy_inc_bosses).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        b_card = ttk.LabelFrame(tab, text=" Boss Scaling Modifications ", padding=10)
        b_card.pack(fill=tk.X, pady=8)
        ttk.Label(b_card, text="Boss Growth Multipliers:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b_card, textvariable=self.boss_growths_mode, values=["false", "random_buff", "random"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(b_card, text="Boss Base Adjustments:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b_card, textvariable=self.boss_stats_mode, values=["false", "1.5", "random_buff", "random"], state="readonly").grid(row=1, column=1, padx=6, sticky=tk.W)
        ttk.Checkbutton(b_card, text="Force Weapon Ranks to S-Rank compatibility", variable=self.boss_max_ranks).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=4)

    # --- Active Config Handling Mechanics ---
    def _collect_ui_to_dict(self):
        """Constructs an explicitly typed dict matching config.yaml specification."""
        return {
            "seed": int(self.seed.get()) if self.seed.get().isdigit() else 0,
            "class_randomization": {
                "mode": self.class_mode.get() if self.class_mode.get() != "false" else False,
                "manakete_count": self.manakete_count.get(),
                "omit_classes": [],
                "include_soldier": self.include_soldier.get(),
                "palette_mapping": self.palette_mapping.get()
            },
            "growth_randomization": {
                "character": self.growth_char.get() if self.growth_char.get() != "false" else False,
                "class": self.growth_class.get() if self.growth_class.get() != "false" else False,
                "class_buff_range": self.growth_buff_range.get(),
                "min": self.growth_min.get(),
                "max": self.growth_max.get(),
                "mean": None,
                "stddev": self.growth_stddev.get(),
                "pool_total": None
            },
            "base_stat_randomization": {
                "character": self.base_char.get() if self.base_char.get() != "false" else False,
                "class": self.base_class.get() if self.base_class.get() != "false" else False,
                "preserve_base": self.base_preserve.get(),
                "shuffle_con_mov": self.base_shuffle_con_mov.get(),
                "cross_tier_scramble": self.base_cross_tier.get(),
                "mean": None,
                "stddev": self.base_stddev.get(),
                "con": {
                    "enabled": self.con_enabled.get(),
                    "min": self.con_min.get(),
                    "player_min": self.con_player_min.get(),
                    "stddev": self.con_stddev.get()
                }
            },
            "item_randomization": {
                "enabled": self.item_enabled.get(),
                "mode": self.item_mode.get(),
                "randomize_events": self.item_rand_events.get()
            },
            "weapon_randomization": {
                "enabled": self.wpn_enabled.get(),
                "might": self.wpn_might.get(),
                "hit": self.wpn_hit.get(),
                "weight": self.wpn_weight.get(),
                "crit": self.wpn_crit.get(),
                "mean": None,
                "stddev": self.wpn_stddev.get(),
                "min_might": self.wpn_min_might.get(),
                "max_might": self.wpn_max_might.get(),
                "min_hit": self.wpn_min_hit.get(),
                "max_hit": self.wpn_max_hit.get()
            },
            "weapon_effects": {
                "enabled": 30 if self.fx_enabled.get() else False,
                "poison": self.fx_poison.get(),
                "nosferatu": self.fx_nosferatu.get(),
                "eclipse": self.fx_eclipse.get(),
                "devil": self.fx_devil.get(),
                "stone": self.fx_stone.get()
            },
            "affinity_randomization": {"enabled": self.affinity_randomization.get()},
            "promotion_items": {
                "enabled": self.promo_enabled.get(),
                "master_seal_universal": self.promo_universal.get(),
                "replace_distribution": self.promo_replace_dist.get()
            },
            "loot_randomization": {
                "enabled": self.loot_enabled.get(),
                "mode": self.loot_mode.get()
            },
            "enemy_randomization": {
                "enabled": self.enemy_enabled.get(),
                "randomize_classes": self.enemy_classes.get(),
                "randomize_items": self.enemy_items.get(), # Typo fixed here
                "randomize_monster_classes": self.enemy_monsters.get(),
                "include_monsters": self.enemy_inc_monsters.get(),
                "include_bosses": self.enemy_inc_bosses.get(),
                "weapon_upgrade_chance": self.enemy_upgrade_chance.get(),
                "omit_classes": [],
                "boss_buffs": {
                    "growths": {"mode": self.boss_growths_mode.get() if self.boss_growths_mode.get() != "false" else False, "buff_range": 0.3, "mean": None, "stddev": 10},
                    "base_stats": {"mode": float(self.boss_stats_mode.get()) if self.boss_stats_mode.get() == "1.5" else (self.boss_stats_mode.get() if self.boss_stats_mode.get() != "false" else False), "buff_range": 0.3, "mean": None, "stddev": 3},
                    "max_weapon_ranks": self.boss_max_ranks.get()
                }
            }
        }

    # --- File Handle & Trigger Functions ---
    def browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("GBA ROMs", "*.gba"), ("All Files", "*.*")])
        if path:
            self.rom_path.set(path)
            if not self.output_path.get():
                base, ext = os.path.splitext(path)
                self.output_path.set(f"{base}_randomized{ext}")

    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".gba", filetypes=[("GBA ROMs", "*.gba")])
        if path: self.output_path.set(path)

    def load_config(self):
        path = filedialog.askopenfilename(filetypes=[("YAML Configuration", "*.yaml;*.yml")])
        if not path: return
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            if "seed" in data: self.seed.set(str(data["seed"]))
            if "class_randomization" in data:
                c = data["class_randomization"]
                self.class_mode.set(c.get("mode") or "false")
                self.manakete_count.set(c.get("manakete_count", 1))
            messagebox.showinfo("Success", "Configuration layout updated successfully from file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed parsing standard YAML structure:\n{e}")

    def save_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML Configuration", "*.yaml")])
        if not path: return
        try:
            out_dict = self._collect_ui_to_dict()
            with open(path, "w") as f:
                yaml.dump(out_dict, f, default_flow_style=False)
            messagebox.showinfo("Success", f"Configuration cleanly written to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export values to disk configuration format:\n{e}")

    def run_randomizer(self):
        if not self.rom_path.get() or not self.output_path.get():
            messagebox.showerror("Validation Error", "Target assignment profiles require explicit Input/Output ROM selections.")
            return

        config_dict = self._collect_ui_to_dict()
        try:
            from randomizer import apply_config
            output_msg = apply_config(
                self.rom_path.get(), 
                config_dict, 
                seed=config_dict["seed"], 
                output_path=self.output_path.get()
            )
            messagebox.showinfo("Success!", "Randomization engine processing finished safely.")
        except Exception as e:
            messagebox.showerror("Engine Failure", traceback.format_exc())

if __name__ == "__main__":
    app = FE8RandomizerGUI()
    app.mainloop()