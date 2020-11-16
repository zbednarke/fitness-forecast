import numpy as np 
import fitbit
import gather_keys_oauth2 as Oauth2
import pandas as pd 
import datetime


class FatlossJourney():
    def __init__(self, day0params: dict):
        """
        day0parms: dict
            dict with keys:
                c: caloric deficit per day
                df: journey length in days
                w0: initial dry weight
                b0: inital bodyfat ratio
                db0: uncertainty in b0
                dw: deficit days per week
                dc_cons_opt: len 2 array
                    actual cal deficit per day - nominal value. conservative and optimistic values.
        """
        self.cals_per_lb = 3500
        self.c = day0params['c']
        self.df = day0params['df']
        self.w0 = day0params['w0']
        self.b0 = day0params['b0']
        self.db0 = day0params['db0']
        self.dw = day0params['dw']
        self.dc_cons_opt = day0params['dc_cons_opt']

        self.days = np.arange(self.df)

        self.data_proj = self.calc_data_proj()

    def calc_data_proj(self):
        
        # calc projection through df
        self.bf_proj_med = self.body_fat_ratio(d=self.days, dc=None, bound=None)
        self.bf_proj_cons = self.body_fat_ratio(d=self.days, dc=None, bound='conservative')
        self.bf_proj_optim = self.body_fat_ratio(d=self.days, dc=None, bound='optimistic')
        self.calc_bf_cdev_bands(self.dc_cons_opt)
        
    def calc_bf_cdev_bands(self, dc_cons_opt):
        dc_cons, dc_opt = dc_cons_opt
        self.bf_proj_cdev_bands = {
            'med_dc_cons': self.body_fat_ratio(d=self.days, dc=dc_cons, bound=None),
            'med_dc_opt': self.body_fat_ratio(d=self.days, dc=dc_opt, bound=None),
            'cons_dc_cons': self.body_fat_ratio(d=self.days, dc=dc_cons, bound='conservative'),
            'cons_dc_opt': self.body_fat_ratio(d=self.days, dc=dc_opt, bound='conservative'),
            'opt_dc_cons': self.body_fat_ratio(d=self.days, dc=dc_cons, bound='optimistic'),
            'opt_dc_opt': self.body_fat_ratio(d=self.days, dc=dc_opt, bound='optimistic')
        }
#         self.weight_proj XXX

#     def calc_bf_proj(self, d=None, bound=None):
#         if d is None:
#             d = self.days
#         return 
        
        
        
        

    def body_fat_ratio(self, d=None, dc=None, bound=None):
        """
        Returns bodyfat ratio at a certain point in fitness journey

        dc: float or None
            actual cal deficit per day - nominal value. Negative means youre eating more.
        d: int
            days into journey
        bound: str or None
            must be in ['conservative', 'optimistic', None]
        """
        if d is None:
            d = self.df
        deltaF = self.get_fat_weight_lost(d, dc=dc, bound=bound)
        Fstar = self.b0 * self.w0
        denom = self.w0 - deltaF
        if bound is None:
            sign = 0
        elif bound == 'conservative':
            sign = -1
        elif bound == 'optimistic':
            sign = 1
        adjust = sign * self.db0 * self.w0
        deltaF = deltaF + adjust
        num = Fstar - deltaF
        return num / denom


    def get_fat_weight_lost(self, d, dc=None, bound=None):
        """
        dc: float or None
            actual cal deficit per day - nominal value. Negative means youre eating more.
        d: int or array
            days at which to evaluate fat loss
        bound: str or None
            must be in ['conservative', 'optimistic', None]
        """
        if dc is None:
            c = self.c
        else:
            c = self.c + dc
        df = np.max(d)
        deficit_days, idxs = np.ones(df + 1), np.arange(df + 1)
        dw = self.dw
        for i in range(7 - dw):
            off_idxs = idxs[(7 - dw + idxs) % 7 - i == 0]
            deficit_days[off_idxs] = 0
        cum_days_deficit = np.cumsum(deficit_days)
        cum_cals_deficit = c * cum_days_deficit
        deltaF = cum_cals_deficit / self.cals_per_lb
        if len(d) == 1:
            return deltaF[df]
        elif len(d) > 1:
            return deltaF[d]
        
    def data_exists(self):
        res = True
        for data in [self.bf_proj_med, self.bf_proj_optim, self.bf_proj_cons] + [a for a in self.bf_proj_cdev_bands.values()]:
            res = (data.size > 0) * res
        return res
        
    def proj_dataframe(self):
        assert self.data_exists()
        df = pd.DataFrame({
            "time": self.days,
            "bf_conservative": self.bf_proj_cons,
            "bf_median": self.bf_proj_med,
            "bf_optimistic": self.bf_proj_optim,
            "bf_median_dc_cons": self.bf_proj_cdev_bands['med_dc_cons'],
            "bf_median_dc_opt": self.bf_proj_cdev_bands['med_dc_opt'],
            "bf_cons_dc_cons": self.bf_proj_cdev_bands['cons_dc_cons'],
            "bf_cons_dc_opt": self.bf_proj_cdev_bands['cons_dc_opt'],
            "bf_opt_dc_cons": self.bf_proj_cdev_bands['opt_dc_cons'],
            "bf_opt_dc_opt": self.bf_proj_cdev_bands['opt_dc_opt']
            
        })
        return df
    
    
    def plot_projection_lines(self, variable='bodyfat ratio', fig=None, show=True, bounds=None):
        df = self.proj_dataframe()
        # Build graph
        if bounds is None:
            y_low, y_high = .05, .2
        else:
            y_low, y_high = bounds
        if variable == 'bodyfat ratio':
            layout = go.Layout(
            title="Bodyfat projections over time",    
            plot_bgcolor="#FFFFFF",
            width=1200,
            height=800,
            legend=dict(
                    # Adjust click behavior
                    itemclick="toggleothers",
                    itemdoubleclick="toggle",
                ),
            xaxis={
                  "linecolor": "#BCCCDC",
                  "side": "bottom",
                  "type": "linear",
                  "ticks": "inside",
                  "title": "Days",
#                   "anchor": "y",
#                   "domain": [
#                     0,
#                     1
#                   ],
                  "mirror": "ticks",
                  "nticks": 8,
                  "showgrid": True,
                  "showline": True,
                  "tickfont": {
                    "size": 10
                  },
                  "zeroline": False,
                  "titlefont": {
                    "size": 10,
                    "color": "#000000"
                  }
                },
            yaxis={
                  "side": "left",
                  "type": "linear",
                  "range": [
                    y_low,
                    y_high
                  ],
                  "ticks": "inside",
                  "title": variable,
                  "anchor": "x",
#                   "domain": [
#                     0,
#                     1
#                   ],
                  "mirror": "ticks",
                  "linecolor": "#BCCCDC",
                  "nticks": 10,
                  "showgrid": True,
                  "showline": True,
                  "tickfont": {
                    "size": 10
                  },
                  "zeroline": False,
                  "titlefont": {
                    "size": 10,
                    "color": "#000000"
                  }
                },
            )
            if fig is None:
                fig = go.Figure(layout=layout)
        
            plotdata = []
            time = df.time
            med = df.bf_median
            cons = df.bf_conservative
            optim = df.bf_optimistic
            ydata = [med, cons, optim]
            names = ["bf0 median", "bf0 conservative", "bf0 optimistic"]
            colors = ['rgba(0,0,255,1)', 'rgba(255,0,0,1)', 'rgba(0,255,0,1)']
            for data, name, color in zip(ydata, names, colors):
                fig = fig.add_trace(go.Scatter(
                    x=time,
                    y=data,
                    name=name,
                    mode='lines',
                    line=dict(color=color),)
                    )
        if show:
            fig.show(config={"displayModeBar": False, "showTips": False})
        return fig
        
        
    def plot_projection_cdev_band(self, fig, variable='bodyfat ratio', bound=None, show=True):
        df = self.proj_dataframe()
        if bound is None:
            nominal = df.bf_median
            cons = df.bf_median_dc_cons
            optim = df.bf_median_dc_opt
            color = 'rgba(0,0,255,.1)'
            
        elif bound == 'conservative':
            nominal = df.bf_median
            cons = df.bf_cons_dc_cons
            optim = df.bf_cons_dc_opt
            color = 'rgba(255,0,0,.1)'
            
        elif bound == 'optimistic':
            nominal = df.bf_median
            cons = df.bf_opt_dc_cons
            optim = df.bf_opt_dc_opt
            color = 'rgba(0,255,0,.1)'
            
        else: 
            raise Exception('Unrecognized bf0 bound.')
        x = df.time.to_list()
        cons = cons.to_list()
        optim = optim.to_list()
#         names = ["bf0 median", "bf0 conservative", "bf0 optimistic"]
        fig = fig.add_trace(
                go.Scatter(
                    x = x + x[::-1], # x, then x reversed
                    y = optim + cons[::-1], # upper, then lower reversed
                    fill='toself',
                    fillcolor=color,
                    line=dict(color=color),
                    hoverinfo="skip",
                    showlegend=False
            )
        )
        if show:
            fig.show(config={"displayModeBar": False, "showTips": False})
        return fig
    
    def plot_projection_cdev_bands(self, fig, variable='bodyfat ratio', show=True):
        fig = self.plot_projection_cdev_band(fig, variable=variable, bound=None, show=False)
        fig = self.plot_projection_cdev_band(fig, variable=variable, bound='conservative', show=False)
        fig = self.plot_projection_cdev_band(fig, variable=variable, bound='optimistic', show=show)
        return fig