import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import traceback
import os


class FE8RandomizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FE8 Sacred Stones Randomizer")
        self.geometry("800x700")
        self.minsize(700, 600)

        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure(".", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("TNotebook", background="#e0e0e0", padding=2)
        self.style.configure("TNotebook.Tab", padding=[12, 4], font=("Segoe UI", 10, "bold"))
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)

        try:
            icon = tk.PhotoImage(file="ai_cat_icon.png")
            self.iconphoto(True, icon)
        except Exception:
            pass

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
        self.class_omit = tk.StringVar(value="BARD")

        # Growth Settings
        self.growth_char = tk.StringVar(value="false")
        self.growth_class = tk.StringVar(value="false")
        self.growth_buff_range = tk.DoubleVar(value=0.5)
        self.growth_min = tk.IntVar(value=0)
        self.growth_max = tk.IntVar(value=100)
        self.growth_stddev = tk.IntVar(value=10)
        self.growth_pool_total = tk.IntVar(value=0)

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
        self.wpn_min_weight = tk.IntVar(value=1)
        self.wpn_max_weight = tk.IntVar(value=20)
        self.wpn_min_crit = tk.IntVar(value=0)
        self.wpn_max_crit = tk.IntVar(value=30)

        # Weapon Effects Weights
        self.fx_enabled = tk.BooleanVar(value=False)
        self.fx_poison = tk.IntVar(value=2)
        self.fx_nosferatu = tk.IntVar(value=3)
        self.fx_eclipse = tk.IntVar(value=1)
        self.fx_devil = tk.IntVar(value=5)
        self.fx_stone = tk.IntVar(value=1)

        # Enemy Settings
        self.enemy_enabled = tk.BooleanVar(value=True)
        self.enemy_rand_classes = tk.BooleanVar(value=True)
        self.enemy_rand_items = tk.BooleanVar(value=True)
        self.enemy_rand_monsters = tk.BooleanVar(value=False)
        self.enemy_inc_monsters = tk.BooleanVar(value=False)
        self.enemy_inc_bosses = tk.BooleanVar(value=False)
        self.enemy_upgrade_chance = tk.IntVar(value=25)
        self.enemy_omit = tk.StringVar()
        self.boss_growths_mode = tk.StringVar(value="false")
        self.boss_stats_mode = tk.StringVar(value="false")
        self.boss_buff_range = tk.DoubleVar(value=0.3)
        self.boss_max_ranks = tk.BooleanVar(value=True)

        self._build_ui()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _build_ui(self):
        top_frame = ttk.LabelFrame(self, text=" ROM Configuration ", padding=12)
        top_frame.pack(fill=tk.X, padx=12, pady=8)

        self._path_row(top_frame, "Input ROM:", self.rom_path, self.browse_input, 0)
        self._path_row(top_frame, "Output ROM:", self.output_path, self.browse_output, 1)

        f_row = ttk.Frame(top_frame)
        f_row.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=4)
        ttk.Label(f_row, text="Seed (0 = random):").pack(side=tk.LEFT)
        ttk.Entry(f_row, textvariable=self.seed, width=10).pack(side=tk.LEFT, padx=6)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self._build_classes_tab()
        self._build_stats_tab()
        self._build_items_tab()
        self._build_weapons_tab()
        self._build_enemies_tab()

        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Load config.yaml", command=self.load_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom, text="Save config.yaml", command=self.save_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom, text="Randomize ROM!", style="Action.TButton", command=self.run_randomizer).pack(side=tk.RIGHT, padx=4)

    def _path_row(self, parent, label, var, cmd, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky=tk.EW, padx=6, pady=4)
        ttk.Button(parent, text="Browse...", command=cmd).grid(row=row, column=2, padx=2)
        parent.columnconfigure(1, weight=1)

    def _scrollable_tab(self, name):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text=name)
        c = tk.Canvas(f, borderwidth=0, highlightthickness=0)
        s = ttk.Scrollbar(f, orient="vertical", command=c.yview)
        inner = ttk.Frame(c, padding=10)
        inner.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        c.create_window((0, 0), window=inner, anchor="nw")
        c.configure(yscrollcommand=s.set)
        c.pack(side="left", fill="both", expand=True)
        s.pack(side="right", fill="y")
        return inner

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_classes_tab(self):
        tab = self._scrollable_tab("Classes")

        card = ttk.LabelFrame(tab, text=" Playable Class Randomization ", padding=10)
        card.pack(fill=tk.X, pady=4)

        ttk.Label(card, text="Mode:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Combobox(card, textvariable=self.class_mode, values=["shuffle", "random"], state="readonly").grid(row=0, column=1, sticky=tk.W, padx=6)

        ttk.Label(card, text="Manakete count:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(card, from_=0, to=10, textvariable=self.manakete_count, width=5).grid(row=1, column=1, sticky=tk.W, padx=6)

        ttk.Label(card, text="Omit classes (comma-sep JID names):").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(card, textvariable=self.class_omit, width=30).grid(row=2, column=1, sticky=tk.W, padx=6)

        ttk.Checkbutton(card, text="Allow Soldier (no promotion path)", variable=self.include_soldier).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(card, text="Auto-map custom palettes to new classes", variable=self.palette_mapping).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(card, text="Randomize support affinities", variable=self.affinity_randomization).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)

    def _build_stats_tab(self):
        tab = self._scrollable_tab("Stats & Growths")

        # Growths -------------------------------------------------------
        g = ttk.LabelFrame(tab, text=" Player Character Growths ", padding=10)
        g.pack(fill=tk.X, pady=4)

        ttk.Label(g, text="Mode:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(g, textvariable=self.growth_char, values=["false", "shuffle", "random", "pool"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(g, text="Stddev:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(g, from_=1, to=50, textvariable=self.growth_stddev, width=6).grid(row=1, column=1, padx=6, sticky=tk.W)

        ttk.Label(g, text="Clamp min / max:").grid(row=2, column=0, sticky=tk.W, pady=2)
        sf = ttk.Frame(g)
        sf.grid(row=2, column=1, sticky=tk.W, padx=6)
        ttk.Spinbox(sf, from_=0, to=255, textvariable=self.growth_min, width=5).pack(side=tk.LEFT)
        ttk.Label(sf, text="/").pack(side=tk.LEFT, padx=4)
        ttk.Spinbox(sf, from_=0, to=255, textvariable=self.growth_max, width=5).pack(side=tk.LEFT)

        ttk.Label(g, text="Pool total (0 = auto):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(g, from_=0, to=500, textvariable=self.growth_pool_total, width=6).grid(row=3, column=1, padx=6, sticky=tk.W)

        # Base Stats ----------------------------------------------------
        b = ttk.LabelFrame(tab, text=" Base Stats ", padding=10)
        b.pack(fill=tk.X, pady=8)

        ttk.Label(b, text="Player mode:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b, textvariable=self.base_char, values=["false", "shuffle", "random"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(b, text="Class mode:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(b, textvariable=self.base_class, values=["false", "shuffle", "random"], state="readonly").grid(row=1, column=1, padx=6, sticky=tk.W)

        ttk.Label(b, text="Stddev:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(b, from_=1, to=20, textvariable=self.base_stddev, width=6).grid(row=2, column=1, padx=6, sticky=tk.W)

        ttk.Checkbutton(b, text="Cross-tier scramble (shuffle mode)", variable=self.base_cross_tier).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(b, text="Include Con/Mov in shuffle", variable=self.base_shuffle_con_mov).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

        con = ttk.LabelFrame(b, text=" Constitution Overrides ", padding=8)
        con.grid(row=5, column=0, columnspan=2, sticky="ew", pady=6, padx=2)

        ttk.Checkbutton(con, text="Enable independent Con control", variable=self.con_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(con, text="Min (class):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(con, from_=1, to=25, textvariable=self.con_min, width=5).grid(row=1, column=1, padx=4, sticky=tk.W)
        ttk.Label(con, text="Min (player):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(con, from_=1, to=25, textvariable=self.con_player_min, width=5).grid(row=2, column=1, padx=4, sticky=tk.W)
        ttk.Label(con, text="Stddev:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(con, from_=1, to=20, textvariable=self.con_stddev, width=5).grid(row=3, column=1, padx=4, sticky=tk.W)

    def _build_items_tab(self):
        tab = self._scrollable_tab("Items & Progression")

        card = ttk.LabelFrame(tab, text=" Unit Inventories ", padding=10)
        card.pack(fill=tk.X, pady=4)

        ttk.Checkbutton(card, text="Auto-adjust inventories for new classes", variable=self.item_enabled).pack(anchor=tk.W, pady=2)
        ttk.Label(card, text="Mode:").pack(anchor=tk.W, padx=15)
        ttk.Combobox(card, textvariable=self.item_mode, values=["random", "shuffle"], state="readonly").pack(anchor=tk.W, padx=25)
        ttk.Checkbutton(card, text="Randomize GiveItem events (slow)", variable=self.item_rand_events).pack(anchor=tk.W, padx=15, pady=2)

        card2 = ttk.LabelFrame(tab, text=" Promotion Items ", padding=10)
        card2.pack(fill=tk.X, pady=4)

        ttk.Checkbutton(card2, text="Unify all promotion items as Master Seals", variable=self.promo_enabled).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(card2, text="Any class can use any Master Seal", variable=self.promo_universal).pack(anchor=tk.W, padx=15)
        ttk.Checkbutton(card2, text="Replace chests/drops/events with Master Seals", variable=self.promo_replace_dist).pack(anchor=tk.W, padx=15)

        card3 = ttk.LabelFrame(tab, text=" Loot Randomization ", padding=10)
        card3.pack(fill=tk.X, pady=4)

        ttk.Checkbutton(card3, text="Randomize chests, houses, events loot", variable=self.loot_enabled).pack(anchor=tk.W, pady=2)
        ttk.Label(card3, text="Mode:").pack(anchor=tk.W, padx=15)
        ttk.Combobox(card3, textvariable=self.loot_mode, values=["random", "shuffle"], state="readonly").pack(anchor=tk.W, padx=25)

    def _build_weapons_tab(self):
        tab = self._scrollable_tab("Weapons & Magic")

        card = ttk.LabelFrame(tab, text=" Stat Randomization ", padding=10)
        card.pack(fill=tk.X, pady=4)

        ttk.Checkbutton(card, text="Enable weapon stat randomization", variable=self.wpn_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(card, text="Might (MT)", variable=self.wpn_might).grid(row=1, column=0, sticky=tk.W, padx=15)
        ttk.Checkbutton(card, text="Hit (HIT)", variable=self.wpn_hit).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(card, text="Weight (WT)", variable=self.wpn_weight).grid(row=2, column=0, sticky=tk.W, padx=15)
        ttk.Checkbutton(card, text="Crit (CRT)", variable=self.wpn_crit).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(card, text="Global stddev:").grid(row=3, column=0, sticky=tk.W, padx=15, pady=4)
        ttk.Spinbox(card, from_=1, to=30, textvariable=self.wpn_stddev, width=5).grid(row=3, column=1, sticky=tk.W, padx=6)

        def _range_row(parent, label, row, min_var, max_var, min_to, max_to):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=15, pady=2)
            f = ttk.Frame(parent)
            f.grid(row=row, column=1, sticky=tk.W, padx=6)
            ttk.Spinbox(f, from_=0, to=min_to, textvariable=min_var, width=4).pack(side=tk.LEFT)
            ttk.Label(f, text="/").pack(side=tk.LEFT, padx=2)
            ttk.Spinbox(f, from_=0, to=max_to, textvariable=max_var, width=4).pack(side=tk.LEFT)

        _range_row(card, "Min/Max Might:", 4, self.wpn_min_might, self.wpn_max_might, 30, 30)
        _range_row(card, "Min/Max Hit:", 5, self.wpn_min_hit, self.wpn_max_hit, 150, 150)
        _range_row(card, "Min/Max Weight:", 6, self.wpn_min_weight, self.wpn_max_weight, 30, 30)
        _range_row(card, "Min/Max Crit:", 7, self.wpn_min_crit, self.wpn_max_crit, 50, 50)

        # Effects -------------------------------------------------------
        fx = ttk.LabelFrame(tab, text=" Random Effects ", padding=10)
        fx.pack(fill=tk.X, pady=8)

        ttk.Checkbutton(fx, text="Enable weapon effects (poison, nosferatu, etc.)", variable=self.fx_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=4)

        effects = [
            ("Poison weight:", self.fx_poison),
            ("Nosferatu weight:", self.fx_nosferatu),
            ("Eclipse weight:", self.fx_eclipse),
            ("Devil weight:", self.fx_devil),
            ("Stone weight:", self.fx_stone),
        ]
        for i, (label, var) in enumerate(effects):
            ttk.Label(fx, text=label).grid(row=i + 1, column=0, sticky=tk.W, pady=2)
            ttk.Spinbox(fx, from_=0, to=100, textvariable=var, width=5).grid(row=i + 1, column=1, padx=6, sticky=tk.W)

    def _build_enemies_tab(self):
        tab = self._scrollable_tab("Enemies & Combat")

        card = ttk.LabelFrame(tab, text=" Generic Enemy Randomization ", padding=10)
        card.pack(fill=tk.X, pady=4)

        ttk.Checkbutton(card, text="Enable enemy randomization", variable=self.enemy_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Checkbutton(card, text="Randomize classes", variable=self.enemy_rand_classes).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=15)
        ttk.Checkbutton(card, text="Randomize items", variable=self.enemy_rand_items).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=15)

        ttk.Label(card, text="Weapon upgrade chance (%):").grid(row=3, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(card, from_=0, to=100, textvariable=self.enemy_upgrade_chance, width=5).grid(row=3, column=1, sticky=tk.W, padx=6)

        ttk.Checkbutton(card, text="Include monsters in class pool", variable=self.enemy_inc_monsters).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=15)
        ttk.Checkbutton(card, text="Randomize existing monster enemies too", variable=self.enemy_rand_monsters).grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=15)
        ttk.Checkbutton(card, text="Include bosses in randomization", variable=self.enemy_inc_bosses).grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=15)

        ttk.Label(card, text="Omit classes (comma-sep JID names):").grid(row=7, column=0, sticky=tk.W, pady=4)
        ttk.Entry(card, textvariable=self.enemy_omit, width=30).grid(row=7, column=1, sticky=tk.W, padx=6)

        # Class Growths -------------------------------------------------
        cg = ttk.LabelFrame(tab, text=" Enemy Class Growth Rates ", padding=10)
        cg.pack(fill=tk.X, pady=4)

        ttk.Label(cg, text="Mode:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(cg, textvariable=self.growth_class, values=["false", "shuffle", "random", "random_buff", "pool"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(cg, text="Stddev:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(cg, from_=1, to=50, textvariable=self.growth_stddev, width=6).grid(row=1, column=1, padx=6, sticky=tk.W)

        ttk.Label(cg, text="Clamp min / max:").grid(row=2, column=0, sticky=tk.W, pady=2)
        sf = ttk.Frame(cg)
        sf.grid(row=2, column=1, sticky=tk.W, padx=6)
        ttk.Spinbox(sf, from_=0, to=255, textvariable=self.growth_min, width=5).pack(side=tk.LEFT)
        ttk.Label(sf, text="/").pack(side=tk.LEFT, padx=4)
        ttk.Spinbox(sf, from_=0, to=255, textvariable=self.growth_max, width=5).pack(side=tk.LEFT)

        ttk.Label(cg, text="Buff range (+/-):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(cg, from_=0.0, to=1.0, increment=0.1, textvariable=self.growth_buff_range, width=6).grid(row=3, column=1, padx=6, sticky=tk.W)

        ttk.Label(cg, text="Pool total (0 = auto):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(cg, from_=0, to=500, textvariable=self.growth_pool_total, width=6).grid(row=4, column=1, padx=6, sticky=tk.W)

        # Boss Buffs ----------------------------------------------------
        bb = ttk.LabelFrame(tab, text=" Boss Buffs (when included) ", padding=10)
        bb.pack(fill=tk.X, pady=8)

        ttk.Label(bb, text="Growths mode:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(bb, textvariable=self.boss_growths_mode, values=["false", "random_buff", "random"], state="readonly").grid(row=0, column=1, padx=6, sticky=tk.W)

        ttk.Label(bb, text="Base stats mode:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(bb, textvariable=self.boss_stats_mode, values=["false", "1.3", "1.5", "random_buff", "random"], state="readonly").grid(row=1, column=1, padx=6, sticky=tk.W)

        ttk.Label(bb, text="Buff range (+/-):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(bb, from_=0.0, to=1.0, increment=0.1, textvariable=self.boss_buff_range, width=5).grid(row=2, column=1, padx=6, sticky=tk.W)

        ttk.Checkbutton(bb, text="Max weapon ranks to S", variable=self.boss_max_ranks).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

    # ------------------------------------------------------------------
    # Config serialization
    # ------------------------------------------------------------------

    def _collect_ui_to_dict(self):
        def _mode(val, allowed):
            return val if val in allowed else False

        def _omit_list(s):
            return [x.strip().upper() for x in s.split(",") if x.strip()]

        bs_val = self.boss_stats_mode.get()
        if bs_val == "false":
            bs_val = False
        elif bs_val not in ("random_buff", "random"):
            try:
                bs_val = float(bs_val)
            except ValueError:
                bs_val = False

        return {
            "seed": int(self.seed.get()) if self.seed.get().isdigit() else 0,
            "class_randomization": {
                "mode": self.class_mode.get(),
                "manakete_count": self.manakete_count.get(),
                "omit_classes": _omit_list(self.class_omit.get()),
                "include_soldier": self.include_soldier.get(),
                "palette_mapping": self.palette_mapping.get(),
            },
            "growth_randomization": {
                "character": _mode(self.growth_char.get(), ["shuffle", "random", "pool"]),
                "class": _mode(self.growth_class.get(), ["shuffle", "random", "random_buff", "pool"]),
                "class_buff_range": self.growth_buff_range.get(),
                "min": self.growth_min.get(),
                "max": self.growth_max.get(),
                "mean": None,
                "stddev": self.growth_stddev.get(),
                "pool_total": self.growth_pool_total.get() if self.growth_pool_total.get() > 0 else None,
            },
            "base_stat_randomization": {
                "character": _mode(self.base_char.get(), ["shuffle", "random"]),
                "class": _mode(self.base_class.get(), ["shuffle", "random"]),
                "preserve_base": self.base_preserve.get(),
                "shuffle_con_mov": self.base_shuffle_con_mov.get(),
                "cross_tier_scramble": self.base_cross_tier.get(),
                "mean": None,
                "stddev": self.base_stddev.get(),
                "con": {
                    "enabled": self.con_enabled.get(),
                    "min": self.con_min.get(),
                    "player_min": self.con_player_min.get(),
                    "stddev": self.con_stddev.get(),
                },
            },
            "item_randomization": {
                "enabled": self.item_enabled.get(),
                "mode": self.item_mode.get(),
                "randomize_events": self.item_rand_events.get(),
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
                "max_hit": self.wpn_max_hit.get(),
                "min_weight": self.wpn_min_weight.get(),
                "max_weight": self.wpn_max_weight.get(),
                "min_crit": self.wpn_min_crit.get(),
                "max_crit": self.wpn_max_crit.get(),
            },
            "weapon_effects": {
                "enabled": 30 if self.fx_enabled.get() else False,
                "poison": self.fx_poison.get(),
                "nosferatu": self.fx_nosferatu.get(),
                "eclipse": self.fx_eclipse.get(),
                "devil": self.fx_devil.get(),
                "stone": self.fx_stone.get(),
            },
            "affinity_randomization": {
                "enabled": self.affinity_randomization.get(),
            },
            "promotion_items": {
                "enabled": self.promo_enabled.get(),
                "master_seal_universal": self.promo_universal.get(),
                "replace_distribution": self.promo_replace_dist.get(),
            },
            "loot_randomization": {
                "enabled": self.loot_enabled.get(),
                "mode": self.loot_mode.get(),
            },
            "enemy_randomization": {
                "enabled": self.enemy_enabled.get(),
                "randomize_classes": self.enemy_rand_classes.get(),
                "randomize_items": self.enemy_rand_items.get(),
                "randomize_monster_classes": self.enemy_rand_monsters.get(),
                "include_monsters": self.enemy_inc_monsters.get(),
                "include_bosses": self.enemy_inc_bosses.get(),
                "weapon_upgrade_chance": self.enemy_upgrade_chance.get(),
                "omit_classes": _omit_list(self.enemy_omit.get()),
                "boss_buffs": {
                    "growths": {
                        "mode": _mode(self.boss_growths_mode.get(), ["random_buff", "random"]),
                        "buff_range": self.boss_buff_range.get(),
                        "mean": None,
                        "stddev": 10,
                    },
                    "base_stats": {
                        "mode": bs_val,
                        "buff_range": self.boss_buff_range.get(),
                        "mean": None,
                        "stddev": 3,
                    },
                    "max_weapon_ranks": self.boss_max_ranks.get(),
                },
            },
        }

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def browse_input(self):
        p = filedialog.askopenfilename(filetypes=[("GBA ROMs", "*.gba"), ("All Files", "*.*")])
        if p:
            self.rom_path.set(p)
            if not self.output_path.get():
                base, ext = os.path.splitext(p)
                self.output_path.set(f"{base}_randomized{ext}")

    def browse_output(self):
        p = filedialog.asksaveasfilename(defaultextension=".gba", filetypes=[("GBA ROMs", "*.gba")])
        if p:
            self.output_path.set(p)

    def load_config(self):
        p = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml;*.yml")])
        if not p:
            return
        try:
            with open(p) as f:
                d = yaml.safe_load(f)
            if not d:
                return

            def _str(v):
                if v is False or v is None:
                    return "false"
                if v is True:
                    return "true"
                return str(v)

            def _bool(v):
                return v is True

            if "seed" in d:
                self.seed.set(str(d["seed"]))

            c = d.get("class_randomization", {})
            if c.get("mode"):
                self.class_mode.set(c["mode"])
            self.manakete_count.set(c.get("manakete_count", 1))
            self.class_omit.set(", ".join(c.get("omit_classes", [])))
            self.include_soldier.set(_bool(c.get("include_soldier")))
            self.palette_mapping.set(c.get("palette_mapping", True))

            g = d.get("growth_randomization", {})
            self.growth_char.set(_str(g.get("character")))
            self.growth_class.set(_str(g.get("class")))
            self.growth_buff_range.set(g.get("class_buff_range", 0.5))
            self.growth_min.set(g.get("min", 0))
            self.growth_max.set(g.get("max", 100))
            self.growth_stddev.set(g.get("stddev", 10))
            self.growth_pool_total.set(g.get("pool_total", 0) or 0)

            b = d.get("base_stat_randomization", {})
            self.base_char.set(_str(b.get("character")))
            self.base_class.set(_str(b.get("class")))
            self.base_preserve.set(b.get("preserve_base", True))
            self.base_shuffle_con_mov.set(b.get("shuffle_con_mov", True))
            self.base_cross_tier.set(b.get("cross_tier_scramble", False))
            self.base_stddev.set(b.get("stddev", 3))
            con = b.get("con", {})
            self.con_enabled.set(con.get("enabled", True))
            self.con_min.set(con.get("min", 1))
            self.con_player_min.set(con.get("player_min", 1))
            self.con_stddev.set(con.get("stddev", 3))

            it = d.get("item_randomization", {})
            self.item_enabled.set(_bool(it.get("enabled")))
            self.item_mode.set(it.get("mode", "random"))
            self.item_rand_events.set(_bool(it.get("randomize_events")))

            w = d.get("weapon_randomization", {})
            self.wpn_enabled.set(_bool(w.get("enabled")))
            self.wpn_might.set(_bool(w.get("might")))
            self.wpn_hit.set(_bool(w.get("hit")))
            self.wpn_weight.set(_bool(w.get("weight")))
            self.wpn_crit.set(_bool(w.get("crit")))
            self.wpn_stddev.set(w.get("stddev", 5))
            self.wpn_min_might.set(w.get("min_might", 1))
            self.wpn_max_might.set(w.get("max_might", 20))
            self.wpn_min_hit.set(w.get("min_hit", 30))
            self.wpn_max_hit.set(w.get("max_hit", 120))
            self.wpn_min_weight.set(w.get("min_weight", 1))
            self.wpn_max_weight.set(w.get("max_weight", 20))
            self.wpn_min_crit.set(w.get("min_crit", 0))
            self.wpn_max_crit.set(w.get("max_crit", 30))

            fx = d.get("weapon_effects", {})
            self.fx_enabled.set(_bool(fx.get("enabled")))
            self.fx_poison.set(fx.get("poison", 2))
            self.fx_nosferatu.set(fx.get("nosferatu", 3))
            self.fx_eclipse.set(fx.get("eclipse", 1))
            self.fx_devil.set(fx.get("devil", 5))
            self.fx_stone.set(fx.get("stone", 1))

            af = d.get("affinity_randomization", {})
            self.affinity_randomization.set(_bool(af.get("enabled")))

            pr = d.get("promotion_items", {})
            self.promo_enabled.set(pr.get("enabled", True))
            self.promo_universal.set(pr.get("master_seal_universal", True))
            self.promo_replace_dist.set(pr.get("replace_distribution", True))

            lr = d.get("loot_randomization", {})
            self.loot_enabled.set(_bool(lr.get("enabled")))
            self.loot_mode.set(lr.get("mode", "random"))

            er = d.get("enemy_randomization", {})
            self.enemy_enabled.set(_bool(er.get("enabled")))
            self.enemy_rand_classes.set(_bool(er.get("randomize_classes")))
            self.enemy_rand_items.set(_bool(er.get("randomize_items")))
            self.enemy_rand_monsters.set(_bool(er.get("randomize_monster_classes")))
            self.enemy_inc_monsters.set(_bool(er.get("include_monsters")))
            self.enemy_inc_bosses.set(_bool(er.get("include_bosses")))
            self.enemy_upgrade_chance.set(er.get("weapon_upgrade_chance", 25))
            self.enemy_omit.set(", ".join(er.get("omit_classes", [])))
            bb = er.get("boss_buffs", {})
            bg = bb.get("growths", {})
            self.boss_growths_mode.set(_str(bg.get("mode")))
            bs = bb.get("base_stats", {})
            bm = bs.get("mode", False)
            if isinstance(bm, (int, float)) and not isinstance(bm, bool):
                self.boss_stats_mode.set(str(bm))
            else:
                self.boss_stats_mode.set(_str(bm))
            self.boss_buff_range.set(bg.get("buff_range", 0.3))
            self.boss_max_ranks.set(bb.get("max_weapon_ranks", True))

            messagebox.showinfo("Loaded", f"Loaded config from {os.path.basename(p)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")

    def save_config(self):
        p = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML", "*.yaml")])
        if not p:
            return
        try:
            with open(p, "w") as f:
                yaml.dump(self._collect_ui_to_dict(), f, default_flow_style=False)
            messagebox.showinfo("Saved", f"Saved to {os.path.basename(p)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")

    def run_randomizer(self):
        if not self.rom_path.get():
            messagebox.showerror("Missing ROM", "Select an input ROM first.")
            return
        if not self.output_path.get():
            base, ext = os.path.splitext(self.rom_path.get())
            self.output_path.set(f"{base}_randomized{ext}")

        cfg = self._collect_ui_to_dict()
        try:
            from randomizer import apply_config
            result = apply_config(self.rom_path.get(), cfg, output_path=self.output_path.get())
            messagebox.showinfo("Done", f"Randomized ROM saved to:\n{result}")
        except Exception:
            messagebox.showerror("Error", traceback.format_exc())


if __name__ == "__main__":
    app = FE8RandomizerGUI()
    app.mainloop()
